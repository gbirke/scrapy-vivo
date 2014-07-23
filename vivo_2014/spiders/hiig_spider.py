from string import join,split
from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http import Request

from vivo_2014.items import Person, Organization, Publication, Lecture, Event

import re

class HiigSpider(Spider):
    name = "hiig_spider"
    allowed_domains = ["www.hiig.de"]
    start_urls = [
        #"http://www.hiig.de/institute/organisation/",
        #"http://www.hiig.de/personen/",
        #"http://www.hiig.de/ausgewahlte-publikationen/" #  sollten wir nicht lieber das Link nehmen: 
        http://www.hiig.de/publikationen-des-hiig/  
    ]

    def parse(self, response):
        if response.url.find("organisation") > -1:
            return self.parse_organization(response)
        if response.url.find("publi") > -1:
            return self.parse_publications(response)
        else:
            return self.parse_overview(response)

    def parse_overview(self, response):
        sel = Selector(response)
        for url in sel.xpath("//ul[@id='menu-staff']/li/ul/li/a/@href").extract():
            yield Request(url, callback=self.parse_person)

    def parse_organization(self, response):
        orga = Organization()
        orga["source_url"] = response.url
        sel = Selector(response)
        # Der Name der Organisation 
        name = join(sel.xpath("/html/head/title/text()").extract(), "")
        name = name.replace("Organisation | ", "")
        orga["name"] = name.strip()
        # TODO: Go to http://www.hiig.de/impressum/ and parse details

        yield orga

    def parse_person(self, response):
        person = Person()
        person["source_url"] = response.url

        sel = Selector(response)
        contact = sel.xpath("//div[@id='secondary']/div[@class='kontakt']/div[@class='var_shbio']")
        name_full = join(sel.xpath("//div[@id='main']/div/div/h1/text()").extract(), "")
        position = join(sel.xpath("//div[@id='secondary']/div[@class='research']/div[@class='staff_position']/text()").extract(), "")
        full_contact_text = join(contact.xpath("text()").extract(), "");

        if name_full.find(",") > -1:
            person["name"], person["title"] = name_full.split(", ")
        else:
            person["name"] = name_full

        # TODO Department und DepartmentRole statt position, wenn position einen Doppelpunkt enthaelt
        # Damit die Departments eindeutig sind und nicht mehrfach erzeugt werden, als source_url fuer Department
        # http://www.hiig.de/institute/organisation/#Department_Name verwenden.
        # Es muss dann noch ein Pipeline-Filter geschrieben werden, der Departments mit der gleichen source_url
        # aussortiert! 
        person["position"] = position
        person["phone"] = re.sub(r".*T.\s+(\+49.0.[-0-9 ]+).*$", "\\1", full_contact_text, flags=re.DOTALL)

        for c in contact.xpath("a"):
            href = join(c.xpath("@href").extract(), "")
            if href.find("mailto:") > -1:
                person["email"] = href.replace("|a|", "@").replace("mailto:", "")
            else:
                person["web"] = href

        yield person

    def parse_publications(self,response):
        
        sel = Selector(response)
        for pub_link in sel.css("#content .publication-APA a"):
            url = pub_link.xpath("@href").extract()[0]
            yield Request(url, callback=self.parse_publication_detail)

    def parse_publication_detail(self,response):
        publi = Publications()
        #publi = response.meta['publi']
        sel = Selector(response)
        infotable = sel.xpath("div[@id='content']/div/table")
        authors = join(infotable.xpath("tr[1]/td[2]/text()").extract(), "")
        publi["author_names"] = authors
        year = join(infotable.xpath("tr[3]/td[2]/text()").extract(), "")
        publi["year"] = year
        pubtype = join(infotable.xpath("tr[4]/td[2]/text()").extract(), "")
        publi["publication_type"] = pubtype
        
        #source_details = join(infotable.xpath("tr[2]/td[2]/text()").extract(), "")
        #source_title = source_details
        #published_in = 
        
