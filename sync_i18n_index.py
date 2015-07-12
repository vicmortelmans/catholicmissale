import webapp2
import spreadsheet_index
import datastore_index
from main import decorator


class SyncI18nTerminologyHandler(webapp2.RequestHandler):

    @decorator.oauth_required
    def get(self):
        # get the contents of the index spreadsheet
        index_i18n_mgr = spreadsheet_index.I18nTerminology(oauth_decorator=decorator)
        self.index_i18n = index_i18n_mgr.sync_table()

        # decompose each row into a set of rows, per language
        index_i18n_flat = flatten(self.index_i18n)

        # get the datastore
        datastore_i18n_mgr = datastore_index.I18n()

        # copy the data in the index to the datastore
        datastore_i18n_mgr.bulkload_table(index_i18n_flat, 'id')

        # feedback to the user
        self.response.out.write("I18n Terminology datastore updated")


class SyncI18nOfHandler(webapp2.RequestHandler):

    @decorator.oauth_required
    def get(self):
        # get the contents of the index spreadsheet
        index_i18n_mgr = spreadsheet_index.I18nOf(oauth_decorator=decorator)
        self.index_i18n = index_i18n_mgr.sync_table()

        # decompose each row into a set of rows, per language
        index_i18n_flat = flatten(self.index_i18n)

        # get the datastore
        datastore_i18n_mgr = datastore_index.I18n()

        # copy the data in the index to the datastore
        datastore_i18n_mgr.bulkload_table(index_i18n_flat, 'id')

        # feedback to the user
        self.response.out.write("I18n Liturgical Days Ordinary Form datastore updated")


class SyncI18nEoHandler(webapp2.RequestHandler):

    @decorator.oauth_required
    def get(self):
        # get the contents of the index spreadsheet
        index_i18n_mgr = spreadsheet_index.I18nEo(oauth_decorator=decorator)
        self.index_i18n = index_i18n_mgr.sync_table()

        # decompose each row into a set of rows, per language
        index_i18n_flat = flatten(self.index_i18n)

        # get the datastore
        datastore_i18n_mgr = datastore_index.I18n()

        # copy the data in the index to the datastore
        datastore_i18n_mgr.bulkload_table(index_i18n_flat, 'id')

        # feedback to the user
        self.response.out.write("I18n Liturgical Days Extraordinary Form datastore updated")


def flatten(table):
    flat_table = []
    for row in table:
        ref = row['ref'] if row['ref'] else ''
        for lang in row.keys():
            if lang != 'ref':
                flat_table.append({
                    'id': lang + '.' + ref,
                    'ref': ref,
                    'lang': lang,
                    'string': row[lang]
                })
    return flat_table