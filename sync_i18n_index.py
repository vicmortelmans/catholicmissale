import webapp2
import spreadsheet_index
import datastore_index


class SyncI18nHandler(webapp2.RequestHandler):
    def get(self):
        # get the contents of the index spreadsheet
        index_i18nTerminology_mgr = spreadsheet_index.I18nTerminology()
        self.index_i18nTerminology = index_i18nTerminology_mgr.sync_table()
        index_i18nOf_mgr = spreadsheet_index.I18nOf()
        self.index_i18nOf = index_i18nOf_mgr.sync_table()
        index_i18nEo_mgr = spreadsheet_index.I18nEo()
        self.index_i18nEo = index_i18nEo_mgr.sync_table()

        # decompose the rows (a list of dicts)
        index_i18n = []
        for table in [self.index_i18nTerminology, self.index_i18nOf, self.index_i18nEo]:
            for row in table:
                ref = row['ref'] if row['ref'] else ''
                for lang in row.keys():
                    if lang != 'ref':
                        index_i18n.append({
                            'id': lang + '.' + ref,
                            'ref': ref,
                            'lang': lang,
                            'string': row[lang]
                        })

        # get the datastore
        datastore_i18n_mgr = datastore_index.I18n()

        # copy the data in the index to the datastore
        datastore_i18n_mgr.bulkload_table(index_i18n, 'id')

        # feedback to the user
        self.response.out.write("I18n datastore updated")
