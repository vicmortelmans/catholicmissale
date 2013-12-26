import webapp2
import model
import logging
import bibleref

logging.basicConfig(level=logging.INFO)

class FlushIllustrationHandler(webapp2.RequestHandler):
    def get(self):
        for key in list(model.Illustration.query().iter(keys_only = True)):
            key.delete()
        self.response.out.write("Flushed all illustrations in datastore!")


class FlushMassHandler(webapp2.RequestHandler):
    def get(self):
        for key in list(model.Mass.query().iter(keys_only = True)):
            key.delete()
        self.response.out.write("Flushed all masses in datastore!")


class FlushI18nHandler(webapp2.RequestHandler):
    def get(self):
        for key in list(model.I18n.query().iter(keys_only = True)):
            key.delete()
        self.response.out.write("Flushed all strings in i18n datastore!")


class Model_index():
    """Read a published google spreadsheet into a list of dicts.
       Each dict is an entity in the datastore.
       Repeated properties are represented as a list.
       The list is then available as the table attribute."""
    def __init__(self, Datastore_model):
        self._Model = Datastore_model
        self.table = []
        #self.sync_table()

    def sync_table(self):
        del self.table[:]  # table = [] would break the references!
        query = self._Model.query()
        for entity in query:
            # convert object to dict
            d = {}
            for a in entity._values:
                d[a] = getattr(entity, a)  # repeated properties are represented as a list
            self.table.append(d)
        return self.table

    def bulkload_table(self, table, key_name):
        """
        @param table: input data as a list of dicts
        @param key_name:
        @return:
        Bulkloading will add new entities, update existing entities, but NOT delete obsolete entities!
        """
        for row in table:
            id = row[key_name]
            # find an entity with ndb key = id
            # if you can't find one, create a new entity with ndb key = id
            # and set the value of the attribute named {key_name} to id as well
            # note that this attribute should be the only required attribute in the ndb model!
            # also note that a key should always be a string!
            entity = self._Model.get_or_insert(str(id), **{key_name: id})
            # overwrite the values of all entities by the values in the table
            for column_name in entity.to_dict():
                if column_name in row:  # dict may be incomplete
                    setattr(entity, column_name, row[column_name])  # repeated properties are represented as a list
            entity.put()
            logging.info('In datastore added/updated row with key= ' + str(id))
        self.sync_table()

    def delete_entities(self, obsolete_entities, key_name):
        for id in obsolete_entities:
            entity = self._Model.get_or_insert(str(id), **{key_name: id})
            entity.key.delete()
            logging.info('In datastore deleted row with key= ' + str(id))
        if obsolete_entities:
            self.sync_table()


class Illustrations(Model_index):
    """Read Illustration entities from the datastore
    into a dict of Illustration objects"""
    def __init__(self):
        Model_index.__init__(self, model.Illustration)

    def bulkload_table(self, table):
        d = {}
        for row in table:
            id = row['id']
            reference = row['passageReference']
            if reference:
                new_reference = bibleref.submit(reference)
                if new_reference:
                    # update the table before bulkloading
                    row['passageReference'] = new_reference
                    d[id] = row
        Model_index.bulkload_table(self, table, 'id')
        return d

    def delete_entities(self, obsolete_entities):
        Model_index.delete_entities(self, obsolete_entities, 'id')

class Masses(Model_index):
    def __init__(self):
        Model_index.__init__(self, model.Mass)

    def bulkload_table(self, table):
        """
        @param table: input data as a list of dicts
        @return: dict of updated rows ad dicts
        """
        d = {}
        for row in table:
            id = row['id']
            for reading_type in ['gospel', 'lecture', 'epistle']:
                references = row[reading_type]  # this is a repeated property !
                if references:
                    for reference in references:
                        new_reference = bibleref.submit(reference)
                        if new_reference:
                            # update the table before bulkloading
                            row[reading_type] = [new_reference if r == reference else r for r in row[reading_type]]
                            # store the updated rows in a dict, for being returned
                            d[id] = row
        Model_index.bulkload_table(self, table, 'id')
        return d

    def delete_entities(self, obsolete_entities):
        Model_index.delete_entities(self, obsolete_entities, 'id')


class I18n(Model_index):
    def __init__(self):
        Model_index.__init__(self, model.I18n)


class Dates(Model_index):
    def __init__(self):
        Model_index.__init__(self, model.Date)

