import webapp2
from jinja_templates import jinja_environment
import spreadsheet_index
import datastore_index
from main import decorator


class SyncMassesHandler(webapp2.RequestHandler):

    @decorator.oauth_required
    def get(self):
        # get the contents of the index spreadsheet
        index_masses_mgr = spreadsheet_index.Masses(oauth_decorator=decorator)
        self.index_masses = index_masses_mgr.sync_table()

        # get the contents of the datastore
        datastore_masses_mgr = datastore_index.Masses()
        self.datastore_masses = datastore_masses_mgr.sync_table()

        # copy the data in the index to the datastore
        # get the rows for which biblerefs are updated during registration
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
        index_ids = [i['id'] for i in self.index_masses]
        for i in self.datastore_masses:
            id = i['id']
            if id not in index_ids:
                d[id] = {}

