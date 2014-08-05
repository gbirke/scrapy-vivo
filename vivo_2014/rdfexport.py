import sys
import rdflib

from rdflib.namespace import RDF, RDFS, FOAF
from rdflib import URIRef, BNode, Literal, XSD

from vivo_2014.items import Person, Division, Organization, Publication
from vivo_2014.names import Name

MyNamespaces = {
    "LOCAL": rdflib.Namespace("http://vivo.mydomain.edu/individual/"),
    "FOAF": rdflib.Namespace("http://xmlns.com/foaf/0.1/"),
    "CORE": rdflib.Namespace("http://vivoweb.org/ontology/core#"),
    "ERO": rdflib.Namespace("http://purl.obolibrary.org/obo/"),
    "VCARD": rdflib.Namespace("http://www.w3.org/2006/vcard/ns#")
}

globals().update(MyNamespaces)

class ExportCollector(object):
    def __init__(self, log):
        self.log = log
        self.graph = rdflib.Graph()
        for url in MyNamespaces:
            if url == "LOCAL":
                continue
            self.graph.bind(url.lower(), MyNamespaces[url])
        self.exporters = {
              Person: PersonExporter(self.graph),
              Organization: OrganizationExporter(self.graph),
              Division: DivisionExporter(self.graph)
            # TODO: Write exporters for the other item types
            #, Publication: PublicationExporter(self.graph)
        }

    def collect(self, item):
        item_type = type(item)
        if item_type in self.exporters:
            self.exporters[item_type].export(item)
        elif item_type == None:
            return
        else:
            self.log("Export of %s not implemented yet." % item_type)

    def get_graph_text(self, format):
        return self.graph.serialize(format=format)

class BaseExporter(object):
    def __init__(self, graph):
        self.graph = graph

    def _get_entry_url(self, type, id, prefix="", suffix=""):
        """ Create a URL for a VIVO "information item" (Person, Individual, organization, etc)
                The URL is added to the graph
        """
        url = self._get_entry_id(id, prefix, suffix)
        self.graph.add( (url, RDF.type, type) )
        return url

    def _get_entry_id(self, id, prefix="", suffix=""):
        urlPattern = "%s%s%s" % (prefix, "%08d", suffix)
        urlId = urlPattern % id
        return LOCAL[urlId]


class PersonExporter(BaseExporter):
    def export(self, item):
        id = item["id"]

        # TODO get person type and replace the default
        personURL = self._get_entry_url(FOAF.NonFacultyAcademic, id, "p")

        if type(item["name"]) == Name:
            label = "%s, %s" % (item['name'].lastname, item['name'].firstname)
            individualNameURL = self._get_entry_url(VCARD.Name, id, "i", "8" )
            self.graph.add( (individualNameURL, VCARD.familyName, Literal(item["name"].lastname)) )
            self.graph.add( (individualNameURL, VCARD.givenName, Literal(item["name"].firstname)) )
            hasName = True
        else:
            label = item["name"]
            hasName = False
        self.graph.add( (personURL, RDFS.label, Literal(label)) )

        hasEmail = False
        if "email" in item and item["email"] != "":
            individualEmailURL = self._get_entry_url(VCARD.Work, id, "i", "1" )
            self.graph.add( (individualEmailURL, RDF.type, VCARD.Email) )
            self.graph.add( (individualEmailURL, VCARD.email, Literal(item["email"])) )
            hasEmail = True

        hasTitle = False
        if "title" in item and item["title"] != "":
            individualTitleURL = self._get_entry_url(VCARD.Title, id, "i", "2" )
            self.graph.add( (individualTitleURL, VCARD.title, Literal(item["title"])) )
            hasTitle = True

        hasPhone = False
        if "phone" in item and item["phone"] != "":
            individualPhoneURL = self._get_entry_url(VCARD.Telephone, id, "i", "4" )
            self.graph.add( (individualPhoneURL, VCARD.telephone, Literal(item["phone"])) )
            hasPhone = True

        # TODO Add web site
        
        individualURL = self._get_entry_url(VCARD.Individual, id, "i")
        self.graph.add( (individualURL, ERO.ARG_2000029, personURL) )
        if hasName:
            self.graph.add( (individualURL, VCARD.hasName, individualNameURL) )
        if hasEmail:
            self.graph.add( (individualURL, VCARD.hasEmail, individualEmailURL) )
        if hasPhone:
            self.graph.add( (individualURL, VCARD.hasTelephone, individualPhoneURL) )
        if hasTitle:
            self.graph.add( (individualURL, VCARD.hasTitle, individualTitleURL) )
        # TODO add name web site urls to this relation
        
        # add Relationship between person and Division
        if "division_role" in item and item["division_role"]:
            role = item["division_role"]
            divisionMembershipURL = self._get_entry_url(CORE.MemberRole, role["id"] , "dm")
            divisionURL = self._get_entry_url(CORE.Division, role["division_id"] , "od")
            self.graph.add( (divisionMembershipURL, RDFS.label, Literal(role["name"])) )
            self.graph.add( (divisionMembershipURL, ERO.RO_0000052, personURL) )
            self.graph.add( (divisionMembershipURL, CORE.roleContributesTo, divisionURL) )
            self.graph.add( (personURL, ERO.RO_0000053, divisionMembershipURL) )
            self.graph.add( (divisionURL, CORE.contributingRole, divisionMembershipURL) )
            
        
        #self.graph.add( (orga_url, ERO.RO_0000052, self._get_entry_id(id, "p")))

        # add organization 
        # TODO Create real position from item["position"]
        # TODO Create independent organization roles similar to divison roles
        # TODO Loop over positions, if an array (ZBW, Klaus Tochtermann)
        position = CORE.NonFacultyAcademicPosition 
        if "position" in item and item["position"] != "":
            position_name = item["position"]
        else:
            position_name = "Wissenschaftlicher Mitarbeiter"
        member_url = self._get_entry_url(position, id, "m")
        self.graph.add( (member_url, RDFS.label, Literal(position_name)) )
        self.graph.add( (member_url, CORE.relates, self._get_entry_id(id, "p")) )
        self.graph.add( (member_url, CORE.relates, self._get_entry_id(item["organization_id"], "o")) )

class OrganizationExporter(BaseExporter):
    def export(self, item):
        id = item["id"]

        orgaURL = self._get_entry_url(FOAF.Organization, id, "o")
        self.graph.add( (orgaURL, RDFS.label, Literal(item["name"])) ) 
        address_fields = {
            "street": "streetAddress",
            "country": "country",
            "postal_code": "postalCode",
            "city": "city"
        }
        vcard_url = None
        for f in address_fields:
            if f in item and item[f] != "":
                if not vcard_url:
                    vcard_url = self._get_entry_url(VCARD.Address, id, "oi", "1")
                self.graph.add( (vcard_url, VCARD[address_fields[f]], Literal(item[f])) )

        web_url = self._get_entry_url(VCARD.URL, id, "oi", "2")
        self.graph.add( (web_url, VCARD.url, Literal(item["source_url"], datatype=XSD.anyURI)) )

        individual_url = self._get_entry_url(VCARD.Individual, id, "oi")
        self.graph.add( (individual_url, RDF.type, VCARD.Kind) )
        self.graph.add( (individual_url, ERO.ARG_2000029, orgaURL) )
        self.graph.add( (individual_url, VCARD.hasURL, web_url) )
        if vcard_url:
            self.graph.add( (individual_url, VCARD.hasAddress, vcard_url) )

class DivisionExporter(BaseExporter):
    def export(self, item):
        id = item["id"]

        divisionURL = self._get_entry_url(CORE.Division, id, "od")
        self.graph.add( (divisionURL, RDFS.label, Literal(item["name"])) ) 
        self.graph.add( (divisionURL, ERO.BFO_0000050, self._get_entry_id(item["organization_id"], "o")) )