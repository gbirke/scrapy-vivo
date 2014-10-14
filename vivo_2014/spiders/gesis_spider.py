from string import join, strip
from urlparse import urljoin
from hashlib import md5
from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http import Request
from scrapy import log

from vivo_2014.items import Person, Division, DivisionRole, Organization, Publication
from vivo_2014.names import NameCollection, LastnameFirstnameSplitter, FirstnameLastnameSplitter

# We use regular expressions
import re

# We use VCard parsing
import vobject

class GesisSpider(Spider):
    name = "gesis_spider"
    allowed_domains = ["www.gesis.org"]
    start_urls = [
        "http://www.gesis.org/das-institut/adresse-und-anreise/standort-koeln/",
        "http://www.gesis.org/forschung/angewandte-informatik-und-informationswissenschaft/",
    ]

    def parse(self, response):
        #return self.parse_research(response)
        if response.url.find("institut") > -1:
            return self.parse_organization(response)
        else:
            return self.parse_overview(response)

    def parse_organization(self, response):
        self.log("Parsing Organization")
        orga = Organization()
        sel = Selector(response)
        orga["source_url"] = response.url
        orga["name"] = u"GESIS - Leibniz-Institut f\xfcr Sozialwissenschaften"
        self.organization = orga

        content = sel.css("#col3 .csc-default")
        address = content.xpath("p[1]/text()").extract()
        orga["street_address"]= strip(address[0])
        city_and_postal_code = re.split("\s+", strip(address[1]), flags=re.UNICODE) # Space can be a nonbreaking space
        orga["postal_code"]= city_and_postal_code[0]
        orga["city"]= city_and_postal_code[1]
        contact = content.xpath("p[2]/text()").extract()
        orga["phone"]= re.search("[-+0-9() ]+",strip(contact[0])).group(0)
        orga["fax"]= re.search("[-+0-9() ]+",strip(contact[1])).group(0)

        yield orga

    def parse_overview(self, response):
        """ Parse start page, branching out to each research subject """
        sel = Selector(response)
        for link in sel.css("#c12546 li a"): 
            url = join(link.xpath("@href").extract(), "") 
            url = self.fix_url(url, response.url)
            yield Request(url, callback=self.parse_research)

    def parse_research(self, response):
        """ 
            Parse each research subject and contact information for the research subject.
            Create new request for each contact 
        """
        division = Division()

        sel = Selector(response)
        division_info = sel.css("#main #col3 .csc-default")

        division["source_url"] = response.url
        division["name"] = join(division_info.css("h1::text").extract(), "")
        description = join(division_info.xpath("p//text()|div/p//text()").extract(), "")
        division["description"] = description
        # The following line does not work because it depends on organization being parsed first, 
        # which cannot be guaranteed
        #division["organization_id"] = self.organization["id"]

        yield division

        contacts = sel.css("#main #col2 .contact")
        for contact in contacts:
            person = Person()
            name = join(contact.xpath("p/strong/a/text()").extract(), "")
            title_match = re.search(r"^((Prof.|Dr.|M.\s*A.)\s*)*", name) # If there are more titles, this will break
            if title_match:
                name = name.replace(title_match.group(0), "")
                person["title"] = strip(title_match.group(0))
            
            splitter = FirstnameLastnameSplitter()
            person.set_name(splitter.get_name(name))

            moreinfo = join(contact.xpath("p/strong/a/@href").extract(), "")

            if moreinfo:
                yield Request(self.fix_url(moreinfo), callback=self.parse_person, meta={
                    'person': person,
                    'division_url': division["source_url"]
                    })
            else:
                yield person

    def parse_person(self, response):
        person = response.meta["person"]
        person["source_url"] = response.url

        # Connect person to division
        division_role = DivisionRole()
        division_role["source_url"] = response.meta["division_url"]
        division_role["name"] = "Leiter" # ACHTUNG Hartcodierung
        division_role["person_url"] = response.url
        division_role["division_url"] = response.meta["division_url"]
        yield division_role

        # TODO Ask students for other fields to parse here

        yield person
        return # Don't do publications while the parsing is broken
        # Parse publication list
        sel = Selector(response)
        publications_list = sel.css(".gs_publication > .gs_publication_list .gs_publication_list")
        current_publication_type = None
        source_url_base = response.url.split("#")[0] + "#" # Remove fragment (regardless if it exists) and add fragment separator
        for item in publications_list:
            current_publication_type = join(item.xpath("h3/text()").extract(), "")
            for pub_item in item.xpath("p"):
                 publication = self.create_publication(pub_item, current_publication_type, source_url_base)
                 # TODO remove person from publication["author_names"] and set publication["author_ids"] instead.
                 if publication:
                    yield publication

    def create_publication(self, publication_item, publication_type, source_url_base):
        """ Create a publication item from publication_item. 
            Which type of publication is created, is determined by publication_type
        """
        pub = Publication()
        text = publication_item.xpath("text()").extract()[0]
        authors_and_year = re.match("(^(.+?)(\d{})", text)
        # TODO 
        if authors_and_year:
            # TODO Parse the new name format with lastname, firstname and firstname lastname, all mixed and separated by commas
            name_collection = NameCollection(LastnameFirstnameSplitter(",")) 
            pub["author_names"] = name_collection.collect(matched.group(1), ";").get_names_list()
            pub["year"] = matched.group(2)
        # TODO remove author and year from text and assign it to title_and_source
        if re.search("Monographien|Forschungs- und Arbeitsberichte|Sonstige Ver.+ffentlichungen|Herausgeberwerke", publication_type):
            title = title_and_source.split(".")[0]
            pub["title"] = strip(title)
            pub["publication_type"] = "Academic Article"
        elif re.search("Referierte Zeitschriftenaufs.+tze|Sammelwerksbeitr.+ge|Zeitschriftenaufs.+tze", publication_type):
            #title
            title = title_and_source.split("In:")[0]
            pub["title"] = strip(title)
            pub["publication_type"] = "Article"
            #source_title
            if re.search("(Hrsg.)",title_and_source):
                source = title_and_source.split("):")[1]# Quelle mit allen Angaben ohne Herausgebernamen
                # source_title = source.split(",")[1]   -macht kein Sinn, da manche Titel auch Kommas enthalten
                pub["published_in"] = strip(source)
                # pub["published_in"] = source_title   - waere in der Kombination mit der vorherigen Kommentar-Zeile
            else:
                source = title_and_source.split("In:")[1]
                source_title = strip(source.split(",")[0])
                pub["published_in"] = strip(source_title)
                
        elif re.search("Vortr.+ge und Veranstaltungen", publication_type):
            #datum = re.search("(((\d{2}\.\s*)?\d{2}\.?\s*-\s*)?(\d{2}\.\s*)?(\d{2}\.?|Januar|Februar|M.+rz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*|[WS]S (\d{4}/)?)?\d{4}[.\s]+$", title_and_source, flags=re.UNICODE)
            title_and_source2 = re.sub("(((\d{2}\.\s*)?\d{2}\.?\s*-\s*)?(\d{2}\.\s*)?(\d{1,2}\.?|Januar|Februar|M.+rz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*|[WS]S (\d{4}/)?)?\d{4}[.\s]+$", "", title_and_source)# title_and_source ohne Datum am Ende
            loc_found = re.search("([^.]+?)[\s.,]+$", title_and_source2)
            pub["publication_type"] = "Conference Paper"
            if loc_found:
                loc = loc_found.group(1)#Ort
                title_and_source3 = title_and_source2.replace(loc_found.group(0), "") # Letzter Satz ohne Ort und Datum
                pub["location"] = loc
            else:
                self.log("loc not found in '%s' url %s" % (title_and_source2, source_url_base), log.WARNING)
                return
            #title_and_source3 = re.sub("([^.]+?)[\s.,]+$", "", title_and_source2)
            published_in_found = re.search(".\s*([^.]+)\.?$", title_and_source3)
            if published_in_found:
                published_in = published_in_found.group(1) #Titel der Quelle
                title = title_and_source3.replace(published_in_found.group(0), "")# Titel der Publikation
                pub["published_in"] = strip(published_in)          
            else:
                self.log("pulished in not found in '%s' for url %s" % (title_and_source3, source_url_base), log.WARNING)
                return
            pub["title"] = strip(title)
            
            
        else:
            self.log("UNKNOWN PUBLICATION TYPE! Type=%s" % publication_type)

        # Extract DOI and download link (which will be used as source url)
        doi_proxy_url = "http://dx.doi.org/"
        for link in publication_item.xpath("a"):
            url = join(link.xpath("@href").extract(), "")
            if re.match(doi_proxy_url, url):
                pub["doi"] = url.replace(doi_proxy_url, "")
            elif re.search("Download", join(link.xpath("text()").extract(), "")):
                pub["source_url"] = url

        # If there is no download link, create a unique ID from the text
        if "source_url" not in pub:
            if "doi" in pub:
                pub["source_url"] = pub["doi"]
            else:
                pub["source_url"] = source_url_base + md5(text.encode('utf-8')).hexdigest()
        return pub

    def fix_url(self, url, current_url=""):
        """ Make URL absolute """
        if url[:4] == "http":
            return url
        elif current_url and url[:3] == "../":
            return urljoin(current_url, url)
        else:
            return urljoin("http://www.gesis.org/" , url)

