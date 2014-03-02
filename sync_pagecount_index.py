import webapp2
import spreadsheet_index
import datastore_index


class SyncPagecountHandler(webapp2.RequestHandler):
    def get(self):
        # get the contents of the index spreadsheet
        index_pagecount_mgr = spreadsheet_index.Pagecount()
        self.index_pagecount = index_pagecount_mgr.sync_table()

        # get the datastore
        datastore_pagecount_mgr = datastore_index.Pagecount()

        # copy the data in the index to the datastore
        datastore_pagecount_mgr.bulkload_table(self.index_pagecount, 'edition')

        # feedback to the user
        self.response.out.write("Pagecount datastore updated")
