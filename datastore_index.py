import model
import logging
import pprint

logging.basicConfig(level=logging.INFO)


class Model_index():
    """Read a published google spreadsheet into a list of dicts.
       Each dict is an entity in the datastore.
       The list is then available as the table attribute."""
    def __init__(self, Model):
        self._Model = Model
        self.sync_table()

    def sync_table(self):
        query = self._Model.query()
        self.table = [object for object in query]

    def bulkload_table(self, table, key_name):
        for row in table:
            entity = self._Model.get_or_insert(row[key_name])
            for column_name in entity.to_dict():
                setattr(entity,column_name,table[column_name])
            entity.put()
            logging.info('In datastore added/updated row ' + pprint.pprint(table))
        self.sync_table()

    def delete_entities(self, obsolete_entities):
        for id in obsolete_entities:
            entity = self._Model.get_or_insert(id)
            entity.key.delete()
            logging.info('In datastore deleted row with key=' + id)
        self.sync_table()


class Illustrations():
    """Read Illustration entities from the datastore
    into a dict of Illustration objects"""
    def __init__(self):
        Model_index.__init__(model.Illustration)

    def bulkload_table(self, table):
        Model_index.bulkload_table(table, 'id')