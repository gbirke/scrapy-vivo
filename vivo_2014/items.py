# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class Person(Item):
    id = Field()
    source_url = Field()
    name = Field()
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
    organization_id = Field() # Reference to Organization
    division_role = Field() # Division Role
    
    # TODO: CV, Description, other fields? Ask students

    # TODO Use Name class with the right splitters in each person crawler and update the RDF export accordingly
    pass

# Used for divisions of an organization, eg. at http://www.zbw.eu/de/forschung/
class Division(Item):
    id = Field()
    source_url = Field()
    name = Field()
    description = Field()
    subject_field = Field() # Schwerpunkt innerhalb der Themenfelder siehe Know Center
    organization_id = Field()

class DivisionRole(Item):
    id = Field()
    source_url = Field()
    name = Field()
    division_url = Field()
    person_url = Field()
    division_id = Field()
    person_id = Field()

# Used for one organization like GESIS or ZBW
class Organization(Item):
    id = Field()
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
    id = Field()
    source_url = Field()
    title = Field()
    publication_date = Field() # komplettes Erscheinungsdatum, wenn vorhanden
    year = Field()# Erscheinungsjahr
    author_urls = Field() # Liste der Autoren, die auch als Person gespeichert wurden (source_url der Person)
    author_names = Field() #Autornamen (Array), die einfach nur als Autoren in VIVO gespeichert werden. Muss noch nachbearbeitet werden
    publication_location = Field() # In welchem Land/Stadt wurde die Veroeffentlichung publiziert
    published_in = Field() # Name des Journals / Events / etc.
    publisher = Field()#Herausgeber / verlag
    organ = Field() # herausgebende Koerperschaft
    startpage = Field() #Startseite
    endpage = Field() #Endseite
    volume = Field() #Band
    issue = Field() #Heft
    doi = Field() # Digital Object Identifier
    phrases = Field() # Schlagwoerter
    thesis_type = Field() #fuer die Hochschulschriften
    publication_type = Field() # Publikationstyp (z.B. )
    abstract = Field() # Beschreibung
    

# Fuer Vortraege s. Know Center
class Lecture(Item):
    id = Field()
    source_url = Field()
    title = Field()
    location_id = Field()
    event_id = Field()
    lecturer_id = Field()
    vispagename = Field()
    vislocs = Field()

#Fuer Konferenzen
class Event(Item):
    id = Field()
    souce_url = Field()
    title = Field()
    location_id = Field()
