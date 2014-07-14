from string import join, strip
from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http import Request

from vivo_2014.items import Person, Division, DivisionRole, Organization

# We use regular expressions
import re

# We use VCard parsing
import vobject

class GesisSpider(Spider):
    name = "gesis_spider"
    allowed_domains = ["www.gesis.org"]
    start_urls = [
        "http://www.gesis.org/forschung/angewandte-informatik-und-informationswissenschaft/",
        "http://www.gesis.org/das-institut/"
        #"http://www.gesis.org/en/research/applied-computer-and-information-science/data-mining-und-knowledge-discovery/"
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
        name = join(sel.css("#main #col3 .csc-default h1::text").extract(), "")
        orga["source_url"] = response.url
        orga["name"] = name
        self.organization = orga

        # TODO Kölner Standort

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

        yield division

        contacts = sel.css("#main #col2 .contact")
        for contact in contacts:
            person = Person()
            name = join(contact.xpath("p/strong/a/text()").extract(), "")
            title_match = re.search(r"^((Prof.|Dr.|M.\s*A.)\s*)*", name) # If there are more titles, this will break
            if title_match:
                person["name"] = name.replace(title_match.group(0), "")
                person["title"] = strip(title_match.group(0))
            else:
                person["name"] = name

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
        address_data = vcard.adr.value.split(";")
        person["street_address"] = address_data[2]
        person["city"] = address_data[3]
        person["postal_code"] = address_data[5]

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
        # TODO Parse publications

        yield person


    def fix_url(self, url):
        """ Make URL absolute """
        if url[:4] != "http":
            url = "http://www.gesis.org/" + url
        return url
