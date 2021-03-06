# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import json
import pprint

from scrapy.item import Item, Field
from vivo_2014.names import Name

def serialize_name(name):
    if type(name) == Name:
        return str(name)
    else:
        return name.encode('utf-8')

def serialize_author_names(names):
    """ Convert Name objects to firstname, lastname lists and export the nested list to JSON"""
    return serialize_to_json([n.to_list() for n in names])

def serialize_to_json(value):
    return json.dumps(value)

class Person(Item):
    source_url = Field()
    name = Field(serializer=serialize_name)
    firstname = Field()
    lastname = Field()
    title = Field()
    email = Field()
    web = Field()
    phone = Field()
    street_address = Field()
    postal_code = Field()
    city = Field()
    country = Field()
    job_description = Field()
    picture = Field() # TODO: Research how to import images in VIVO when doing and RDF import. Shall the images be downloaded and this field contains a reference to the file?
    person_type = Field() # TODO: Where does this come from? Must be from class group "People", should default to "Person"
    position = Field()
    department = Field() # Should this be a reference? Should the Department belong to Organization?
    organization_url = Field() # Reference to Organization
    division_role = Field() # Division Role
    
    # TODO: CV, Description, other fields? Ask students

    # TODO Use Name class with the right splitters in each person crawler and update the RDF export accordingly

    def set_name(self, name):
        self["name"] = name
        self["firstname"] = name.firstname
        self["lastname"]  = name.lastname


# Used for divisions of an organization, eg. at http://www.zbw.eu/de/forschung/
class Division(Item):
    source_url = Field()
    name = Field()
    description = Field()
    subject_field = Field() # Schwerpunkt innerhalb der Themenfelder siehe Know Center
    organization_id = Field()

class DivisionRole(Item):
    source_url = Field()
    name = Field()
    division_url = Field()
    person_url = Field()

# Used for one organization like GESIS or ZBW
class Organization(Item):
    source_url = Field()
    name = Field()
    description = Field()
    web = Field()
    phone = Field()
    fax = Field()
    street_address = Field()
    postal_code = Field()
    city = Field() 
    country = Field()
    email = Field()   

class Publication(Item):
    source_url = Field()
    title = Field()
    publication_date = Field() # komplettes Erscheinungsdatum, wenn vorhanden
    year = Field()# Erscheinungsjahr
    author_urls = Field(serializer=serialize_to_json) # Liste der Autoren, die auch als Person gespeichert wurden (source_url der Person)
    author_names = Field(serializer=serialize_author_names) #Autornamen (Array), die einfach nur als Autoren in VIVO gespeichert werden. Muss noch nachbearbeitet werden
    publication_location = Field() # In welchem Land/Stadt wurde die Veroeffentlichung publiziert
    published_in = Field() # Name des Journals / Events / etc.
    publisher = Field()#Herausgeber / verlag
    organ = Field() # herausgebende Koerperschaft
    startpage = Field() #Startseite
    endpage = Field() #Endseite
    volume = Field() #Band
    issue = Field() #Heft
    download_link = Field() # Wo die Publikation runtergeladen werden kann
    doi = Field() # Digital Object Identifier
    phrases = Field() # Schlagwoerter
    thesis_type = Field() #fuer die Hochschulschriften
    publication_type = Field() # Publikationstyp (z.B. )
    abstract = Field() # Beschreibung
    location = Field() # Veroeffentlichungsort 
    

# Fuer Vortraege s. Know Center und GESIS
class Lecture(Item):
    source_url = Field()
    title = Field()
    location = Field() # Ortsname
    event_id = Field()
    lecturer_id = Field()
    vispagename = Field()
    vislocs = Field()

#Fuer Konferenzen
class Event(Item):
    souce_url = Field()
    title = Field()
    location = Field()
