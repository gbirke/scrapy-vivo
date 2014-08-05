# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import sqlite3

from vivo_2014.items import Organization
from vivo_2014.rdfexport import ExportCollector

class Vivo2014Pipeline(object):
    def process_item(self, item, spider):
        return item

class Item2RDFPipeline(object):
    """ This pipeline stores items in an RDF N3 file.
    """

    def open_spider(self, spider):
        self.collector = ExportCollector(spider.log)

    def close_spider(self, spider):
        file = open('%s_items.n3' % spider.name, 'w+b')
        file.write(self.collector.get_graph_text("n3"))
        file.close()

    def process_item(self, item, spider):
        self.collector.collect(item)
        return item
    

class OrganizationAssignmentPipeline(object):
    """Assign organization_id to items"""

    def open_spider(self,spider):
        self.items = []
        self.organization_id = None
    
    def process_item(self, item, spider):
        if self.organization_id:
            if "organization_id" in item.fields:
                item["organization_id"] = self.organization_id
        else:
            if type(item) == Organization:
                self.organization_id = item["id"]
                for i in self.items:
                    self.items[i]["organization_id"] = self.organization_id
                self.items = []
            else:
                self.items.append(item)
        return item


class Url2IdPipeline(object):
    """ This pipeline stores a numerical ID for every URL item ID in a SQLITE database.

    """

    def open_spider(self, spider):
        self.conn = sqlite3.connect("url_ids.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS item_ids (
            source_url TEXT,
            item_type TEXT,
            id INTEGER,
            PRIMARY KEY (source_url, item_type)
            )
        """)

    def process_item(self, item, spider):
        if item["source_url"] == "":
            return

        item_type = item.__class__.__name__
        item["id"] = self._get_id_for_item(item["source_url"], item_type)
        
        if item_type == "Person" and "division_role" in item:
            self._assign_division_role_ids(item)

        return item

    def _assign_division_role_ids(self, item):
        role = item["division_role"]
        if role["person_url"] == "" or role["division_url"] == "":
            item["division_role"] = None
            return
        role["id"] = self._get_id_for_item(role["source_url"], "DivisionRole")
        role["person_id"] = item["id"]
        role["division_id"] = self._get_id_for_item(role["division_url"], "Division")
        item["division_role"] = role

    def _get_id_for_item(self, source_url, item_type):
        id = self._get_existing_id_for_item(source_url, item_type)
        if id:
            return id
        else:
            return self._create_new_id_for_item(source_url, item_type)

    def _get_existing_id_for_item(self, source_url, item_type):
        self.cursor.execute("SELECT id FROM item_ids WHERE source_url=? AND item_type=?", (source_url, item_type,))
        row = self.cursor.fetchone()
        if row:
            return row[0]
        else:
            return None

    def _create_new_id_for_item(self, source_url, item_type):
        self.cursor.execute("SELECT MAX(id) FROM item_ids WHERE item_type=?", (item_type,))
        row = self.cursor.fetchone()
        if row[0]:
            id = row[0] + 1
        else:
            id = 1
        self.cursor.execute("INSERT INTO item_ids (source_url, item_type, id) VALUES(?,?,?)", (source_url, item_type, id))
        self.conn.commit()
        return id

