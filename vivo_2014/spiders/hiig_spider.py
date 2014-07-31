from string import join,split
from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http import Request

from vivo_2014.items import Person, Organization, Publication, Lecture, Event
from vivo_2014.names import *

import re

class HiigSpider(Spider):
    name = "hiig_spider"
    allowed_domains = ["www.hiig.de"]
    start_urls = [
        #"http://www.hiig.de/institute/organisation/",
        #"http://www.hiig.de/personen/",
        "http://www.hiig.de/publikationen-des-hiig/",
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
        for pub_content in sel.css("#content .publication-APA"):
            pubtype = join(pub_content.xpath("preceding::h3[1]/text()").extract(), "")
            public = Publication()
            
            pub_content_texte = pub_content.xpath("text()").extract()
            autoren_und_titel = pub_content_texte[0]
            autoren = autoren_und_titel.split("(")[0]
            name_collector = NameCollection(LastnameFirstnameSplitter(","))
            public["author_names"] = name_collector.get_names_list(autoren, "\.,|&")
            jahreszahl_und_titel = autoren_und_titel.split("(")[1]
            year_match = re.search("([0-9]{4})\)", jahreszahl_und_titel)
            if year_match:
                public["year"] = year_match.group(1)
            if re.search("Wissenschaftliche Artikel", pubtype):
                title = split(autoren_und_titel, ").")[1]
                public["title"] = title
                pub_content_source = pub_content.xpath("em/text()").extract()
                public["published_in"] = pub_content_source
                public["publication_type"] = "Academic Article"
            elif re.search("B.+cher", pubtype):
                pub_book_title = join(pub_content.xpath("em/text()").extract(), "")
                public["title"] = pub_book_title                
                public["publication_type"] = "Book"
            elif re.search("Buchbeitr.+ge", pubtype):
                titel_und_quelle = split(autoren_und_titel, ").")[1]
                public["title"] = titel_und_quelle.split("In")[0]
                source_autoren = titel_und_quelle.split("In")[1]# ob wir das brauchen
                public["published_in"] = pub_content.xpath("em/text()").extract()
                pages_and_publisher = pub_content_texte[1]
                pages_match = re.search("pp.([0-9]+)\-([0-9]+)", pages_and_publisher)
                if pages_match:
                    public["startpage"] = pages.group(1)
                    public["endpage"] = pages.group(2)
            elif re.search("Sonstige Publikationen", pubtype):
                title = split(autoren_und_titel, "\d).")[1] # Hier gibt es einen Fehler, willst du das 1. oder 2. element? Das 1. hat Index 0
				#ich wollte autoren und titel splitten an der Stelle wo "Ziffer)." steht und den zweiten Element davon nehmen
                public["title"] = title
                pub_content_source = pub_content.xpath("em/text()").extract()
                public["published_in"] = pub_content_source
            else:
                self.log("UNKNOWN PUBLICATION TYPE!")
                

            url = pub_content.xpath("a/@href").extract()[0]
            public["source_url"] = url
            
            yield Request(url, callback=self.parse_publication_detail, meta={"publi": public})

    def parse_publication_detail(self,response):
        publi = response.meta['publi']
        sel = Selector(response)
        
        infotable = sel.css("#content").xpath("div/table")
        authors = join(infotable.xpath("tr[1]/td[2]/span/text()").extract(), "")
        name_collector = NameCollection(LastnameFirstnameSplitter(",\s*")) # wie weiss name_collector, fuer welche Spalte er das macht?
        publi["author_names"] = name_collector.get_names_list(authors, "\.,|&")
        year = join(infotable.xpath("tr[3]/td[2]/span/text()").extract(), "").strip()
        publi["year"] = year
        pubtype = join(infotable.xpath("tr[4]/td[2]/span/text()").extract(), "").strip()
        publi["publication_type"] = pubtype
        if re.search("Buchbeitr.+ge", pubtype):
            source = infotable.xpath("tr[2]/td[2]/span/text()").extract()
            pages_and_puplisher = source[1]
            publi["publisher"] = split(pages_and_publisher, ":")[1]
            # publi["publisher"] = split(source[1], ":")[1]
            publi["published_in"] = infotable.xpath("tr[2]/td[2]/span/em/text()").extract()
            
        yield publi
        
