import model
import logging
import pprint

logging.basicConfig(level=logging.INFO)

class Model_index():
    """Read a published google spreadsheet into a list of dicts.
       Each dict is an entity in the datastore.
       The list is then available as the table attribute."""
    def __init__(self, Model):
        self.Model = Model
        query = Model.query()
        self.table = [object for object in query]

    def bulkload_table(self, table, key_name):
        for row in table:
            entity = self.Model.get_or_insert(row[key_name])
            for column_name in entity.to_dict():
                setattr(entity,column_name,table[column_name])
            entity.put()
            logging.info('In datastore added/updated row ' + pprint.pprint(table))


class Illustrations():
    """Read Illustration entities from the datastore
    into a dict of Illustration objects"""
    def __init__(self):
        super(Illustrations,self).__init__(Illustration)

    def bulkload_table(self, table):
        super(Illustrations,self).bulkload_table(table, 'id')