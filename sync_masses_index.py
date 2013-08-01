import webapp2
from jinja_templates import jinja_environment
import spreadsheet_index
import datastore_index


class SyncMassesHandler(webapp2.RequestHandler):
    def get(self):
        # get the contents of the index spreadsheet
        index_masses_mgr = spreadsheet_index.Masses()
        self.index_masses = index_masses_mgr.table

        # get the contents of the datastore
        datastore_masses_mgr = datastore_index.Masses()
        self.datastore_masses = datastore_masses_mgr.table

        # copy the data in the index to the datastore
        # get the rows that are updated (i.e. biblereferences are updated)
        updated_index_rows = datastore_masses_mgr.bulkload_table(self.index_masses)

        # update the spreadsheet index entries
        index_masses_mgr.update_fields(updated_index_rows)

        # find obsolete datastore entities (no spreadsheet index entry with same id)
        obsolete_entities = {}
        self.find_obsolete_entities(obsolete_entities)

        # delete the obsolete datastore entities
        datastore_masses_mgr.delete_entities(obsolete_entities)

        # the app redirects the user to the index
        template = jinja_environment.get_template('list-masses.html')
        self.response.out.write(template.render(masses=self.datastore_masses))

    def find_obsolete_entities(self, d):
        index_ids = [i['key'] for i in self.index_masses]
        for i in self.datastore_masses:
            key = i['key']
            if key not in index_ids:
                d[key] = {}

