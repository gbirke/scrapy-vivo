from string import join, strip
from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http import Request

from vivo_2014.items import Person, Division, DivisionRole, Organization

import re

class ZbwSpider(Spider):
    name = "zbw_spider"
    allowed_domains = ["www.zbw.eu"]
    start_urls = [
       # "http://www.zbw.eu/de/forschung/",
        "http://www.zbw.eu/de/impressum/"
    ]

    def parse(self, response):
        if response.url.find("impressum") > -1: 
            return self.parse_organization(response)
        else:
            return self.parse_overview(response)

    def parse_organization(self, response):
        orga = Organization()
        orga["source_url"] = response.url
        sel = Selector(response)
        content = sel.css("#c165") # This is very brittle!!! But probably there is no better way to get to right element
        names = content.xpath("p[1]/text()").extract()
        orga["name"] = strip(names[0]) # ignore text following the <br>

        # TODO parse address data
        address = content.xpath("p[2]/text()").extract()
        orga["street_address"]= strip(address[0])
        orga["postal_code"]= strip(address[1]).split(" ")[0]
        orga["city"]= strip(address[1]).split(" ")[1]
        contact = content.xpath("p[3]/text()").extract()
        orga["phone"]= re.search("[-+0-9]+",strip(contact[0])).group(0)
        orga["fax"]= re.search("[-+0-9]+",strip(contact[1])).group(0)
        mail = content.xpath("p[3]/a/text()").extract()
        orga["email"] = join(mail,"")
        yield orga

    def parse_overview(self, response):
        """ Parse start page, branching out to each division subject """
        sel = Selector(response)
        for link in sel.css("#content_main .csc-default.box .bodytext a"):
            url = join(link.xpath("@href").extract(), "")
            url = self.fix_url(url)
            yield Request(url, callback=self.parse_division)

    def parse_division(self, response):
        """ 
            Parse each division and contact information for the division.
            Create new request for each contact 
        """
        division = Division()
        person = Person()

        sel = Selector(response)
        division_info = sel.css("#content_main .csc-default.box")

        division["source_url"] = response.url
        division["name"] = join(division_info.css(".csc-firstHeader::text").extract(), "")
        description = join(division_info.xpath("p//text()").extract(), "")
        description = re.sub(r"@\s*remove-this.\s*", "@", description) # Remove spam protection text
        division["description"] = description

        # This will send the division to the item pipeline where it will get an ID
        yield division 
        
        # Parse person data
        vcard = sel.css("#content_right .vcard")
        # TODO decode encrypted email address
        person["name"] = join(vcard.css(".name .fn::text").extract(), "")
        person["title"] = join(vcard.css(".title::text").extract(), "")
        phone = join(vcard.css(".tel::text").extract(), "")
        phone = re.sub(re.compile(r"^T:\s*", re.U), "", strip(phone)) # Need unicode flag because string contains nonbreaking space
        person["phone"] = phone
        person["street_address"] = join(vcard.css(".adr .street-address::text").extract(), "")
        person["postal_code"] = join(vcard.css(".adr .postal-code::text").extract(), "")
        person["city"] = join(vcard.css(".adr .locality::text").extract(), "")
        url = join(vcard.xpath("a[@class='url']/@href").extract(), "")
        url = self.fix_url(url)

        # Connect person to division
        division_role = DivisionRole()
        division_role["source_url"] = response.url
        division_role["name"] = "Leiter" # ACHTUNG Hartcodierung
        division_role["person_url"] = url
        division_role["division_url"] = response.url
        person["division_role"] = division_role

        yield Request(url, callback=self.parse_person, meta={'person': person})

    def parse_person(self, response):
        """ Add more information to each division contact """
        person = response.meta["person"]
        person["source_url"] = response.url

        sel = Selector(response)
        for b in sel.css("#content_main .csc-default.box"):
            title = join(b.css(".csc-header h2::text").extract(), "")
            #self.log("title is '%s'" % title)
            if title == "Funktion":
                positions = []
                # Manche Positionen sind in <p> Tags (weil Persion nur eine Funktion hat), manche sind in einer Liste.
                p_position = join(b.xpath("p/descendant-or-self::*/text()").extract(), "")
                if p_position:
                    positions = positions + [p_position]
                positions = positions + b.xpath("ul/li/text()").extract()
                person["position"] = positions

        # TODO weitere Daten (Beruflicher Hintergrund (CV), Mitgliedschaften, etc)
        # TODO Publikationen (neuer Request)
        yield person

    def fix_url(self, url):
        """ Make URL absolute """
        if url[:4] != "http":
            url = "http://www.zbw.eu" + url
        return url
