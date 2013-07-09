import model
import logging

logging.basicConfig(level=logging.INFO)


class Model_index():
    """Read a published google spreadsheet into a list of dicts.
       Each dict is an entity in the datastore.
       The list is then available as the table attribute."""
    def __init__(self, Datastore_model):
        self._Model = Datastore_model
        self.table = []
        self.sync_table()

    def sync_table(self):
        del self.table[:]  # table = [] would break the references!
        query = self._Model.query()
        for object in query:
            # convert object to dict
            d = {}
            for a in object._values:
                d[a] = getattr(object, a)
            self.table.append(d)

    def bulkload_table(self, table, key_name):
        for row in table:
            id = row[key_name]
            entity = self._Model.get_or_insert(id, id=id)
            for column_name in entity.to_dict():
                setattr(entity,column_name,row[column_name])
            entity.put()
            logging.info('In datastore added/updated row with key= ' + id)
        self.sync_table()

    def delete_entities(self, obsolete_entities):
        for id in obsolete_entities:
            entity = self._Model.get_or_insert(id, id=id)
            entity.key.delete()
            logging.info('In datastore deleted row with key= ' + id)
        if obsolete_entities:
            self.sync_table()


class Illustrations(Model_index):
    """Read Illustration entities from the datastore
    into a dict of Illustration objects"""
    def __init__(self):
        Model_index.__init__(self, model.Illustration)

    def bulkload_table(self, table):
        Model_index.bulkload_table(self, table, 'id')