# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request

import json
import urlparse
import urllib
import logging

from vivo_2014.items import Person, Division, DivisionRole, Organization, Publication
from vivo_2014.names import *

class KnowcenterSpider(scrapy.Spider):

    # Extracted from data
    # TODO: Create assignment to VIVO publication types
    PublicationTypeIDs = {
        1: u'Academic Article', 
        2: u'Conference Paper', 
        3: u'Academic Article', 
        4: u'Conference Paper', 
        5: u'Chapter', 
        6: u'Conference Poster', 
        7: u'Edited Book', 
        8: u'Proceedings'
    }

    JSONFields = {
        u'title_DE': 'title',
        u'publisher': 'published_in', 
        u'publicationType_DE' : None, 
        u'organ': 'organ', 
        u'vispagename': 'source_url', 
        u'documentPhrases': 'phrases', 
        u'phrases': None, 
        u'year': 'year', 
        u'downloadLink': 'download_link', 
        u'band': 'issue', 
        u'publicationType_EN':None, 
        u'location': 'location', 
        u'authors': 'author_names', 
        u'publicationTypeId': 'publication_type'
    }


    name = "knowcenter_spider"
    allowed_domains = ["oldknowsite.know-center.tugraz.at"]
    start_urls = (
        'http://oldknowsite.know-center.tugraz.at/',
    )

    def parse(self, response):
        yield Request("http://oldknowsite.know-center.tugraz.at/wp-content/visualisation-output/publications/publications.json", callback=self.parse_publications)


    def parse_publications(self, response):
        field_functions = {}
        for f in self.JSONFields:
            function_name = "_parse_field_{}".format(f)
            if hasattr(self, function_name):
                field_functions[f] = getattr(self, function_name)
            else:
                field_functions[f] = lambda v, d: v
        json_data = json.loads(response.body)
        for doc in json_data['DataSet']['documents']['document']:
            pub = Publication()
            for feature in doc['features']['feature']:
                if not self.JSONFields[feature["@id"]]:
                    continue
                field_key = self.JSONFields[feature["@id"]]
                if type(feature['values']) == dict and 'value' in feature['values']:
                    pub[field_key] = field_functions[feature["@id"]](feature['values']['value'], doc)
                elif type(feature['values']) == str and feature['values']:
                    pub[field_key] = field_functions[feature["@id"]](feature['values'], doc)
            yield pub


    def _parse_field_publicationTypeId(self, value, doc):
        try:
            return self.PublicationTypeIDs[value]
        except ValueError:
            self._log("Unknown publication type {}".format(value), logging.ERROR)
            return "Academic Article"
        

    def _parse_field_vispagename(self, value, doc):
        filename = "{}.html".format(urllib.quote(value.encode('utf-8')))
        return urlparse.urljoin(
            "http://oldknowsite.know-center.tugraz.at/publikationen/",
            filename
        )

    def _parse_field_authors(self, value, doc):
        """ Return Authors as array of Name objects by using a splitter """
        if type(value) == str or type(value) == unicode:
            value = [value]
        splitter = LastnameFirstnameSplitter()
        return map(lambda n: splitter.get_name(n), value)

    def _parse_field_publisher(self, value, doc):
        if type(value) == list and len(value) > 0:
            return value[-1]
        return value

    def _parse_field_documentPhrases(self, value, doc):
        if type(value) != list:
            value = []
        phrases = self._get_value_from_doc(doc, "phrases")
        if phrases and type(phrases) == list:
            value += phrases
        return u",".join(phrases)

    def _parse_field_organ(self, value, doc):
        if type(value) == list:
            return u", ".join(map(lambda v: unicode(v), value))
        else:
            return value

    def _get_feature_from_doc(self, doc, name):
        return [f for f in doc['features']['feature'] if f['@id'] == name][0]

    def _get_value_from_doc(self, doc, name):
        v = self._get_feature_from_doc(doc, name)['values']
        if type(v) == str or type(v) == unicode:
            return v
        else:
            return v['value']
