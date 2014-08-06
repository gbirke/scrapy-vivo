from string import join, strip
from hashlib import md5
from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http import Request

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
            url = self.fix_url(url)
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
        # TODO: Why is description empty for "Web Science and Web Technologies" and "Web Science and Web Technologies"? debug xpath and fix it
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
            person["name"] = splitter.get_name(name)

            moreinfo = join(contact.xpath("p/strong/a/@href").extract(), "")

            links = contact.xpath("p/a/@href").extract()
            for l in links:
                if l.find("vcard.php") > -1:
                    url = self.fix_url(l)
                    yield Request(url, callback=self.parse_vcard, meta={
                        'person': person, 
                        'moreinfo': self.fix_url(moreinfo),
                        'division_url': response.url
                        })

    def parse_vcard(self, response):
        person = response.meta["person"]
        vcard = vobject.readOne(response.body)
        person["email"] = vcard.email.value
        if hasattr(vcard, "tel"):
            person["phone"] = vcard.tel.value
        # address_data = vcard.adr.value.split(";")
        # person["street_address"] = address_data[2]
        # person["city"] = address_data[3]
        # person["postal_code"] = address_data[5]

        url = response.meta["moreinfo"]
        if url:
            yield Request(url, callback=self.parse_person, meta={
                'person': person,
                'division_url': response.meta['division_url']
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
        person["division_role"] = division_role

        # TODO Ask students for other fields to parse here

        yield person
        #return
        # Parse publication list
        sel = Selector(response)
        publications_and_headings = sel.css("#staffPublications").xpath('a[@name]|ul[@class="pubResultList"]')
        current_publication_type = None
        source_url_base = response.url.split("#")[0] + "#" # Remove fragment (regardless if it exists) and add fragment separator
        for item in publications_and_headings:
            tag_name = join(item.xpath("name()").extract(), "")
            if tag_name == "a":
                current_publication_type = join(item.xpath("h3/text()").extract(), "")
            elif tag_name == "ul":
                for pub_item in item.xpath("li"):
                     publication = self.create_publication(pub_item, current_publication_type, source_url_base)
                     # TODO remove person from publication["author_names"] and set publication["author_ids"] instead.
                     yield publication

    def create_publication(self, publication_item, publication_type, source_url_base):
        """ Create a publication item from publication_item. 
            Which type of publication is created, is determined by publication_type
        """
        # TODO check publication_type with regex and create different items than just Publication
        pub = Publication()
        text = publication_item.xpath("text()").extract()[0]
        authors_and_year = text.split(":")[0]
        matched = re.match("([^(]+)\((\d+)", authors_and_year)
        if matched:
            name_collection = NameCollection(LastnameFirstnameSplitter(","))
            pub["author_names"] = name_collection.collect(matched.group(1), ";").get_names_list()
            pub["year"] = matched.group(2)
        title_and_source = text.split("):")[1]
        founded = re.search("In:",title_and_source)
        ort_datum = re.search(". (\w+),[-.0-9 ]+$", title_and_source, flags=re.UNICODE)
        if founded:
            #source_title
            source = title_and_source.split("In:")[1]
            source_title = strip(source.split(",")[0])
            pub["published_in"] = source_title
            #title
            title = title_and_source.split("In:")[0]
            pub["title"] = title
        elif ort_datum:
            title_and_source2 = title_and_source.replace(ort_datum.group(0), "")
            published_in = re.search(".\s*([^.]+)$", title_and_source2).group(1) # published_in - Letzter Satz ohne Ort und Datum
            title = title_and_source2.replace(published_in, "")
        else:
            title = title_and_source.split(".")[0]
            pub["title"] = title
        # TODO: Fill in title and other information

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
            pub["source_url"] = source_url_base + md5(text.encode('utf-8')).hexdigest()
        return pub

    def fix_url(self, url):
        """ Make URL absolute """
        if url[:4] != "http":
            url = "http://www.gesis.org/" + url
        return url
