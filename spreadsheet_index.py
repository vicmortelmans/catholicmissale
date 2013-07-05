import webapp2
from jinja_templates import jinja_environment
from gdata.spreadsheets.client import SpreadsheetsClient
from gdata.spreadsheets.data import ListEntry
import google_credentials
# USERNAME = ''
# PASSWORD = ''
import logging
import pprint

logging.basicConfig(level=logging.INFO)

google_spreadsheet_missale_illustrations_key = "0Au659FdpCliwdEtYWm81eEMwUGQ1RlMybUx2UU5BLXc"
google_spreadsheet_first_worksheet_id = 'od6'


class ListSpreadsheetHandler(webapp2.RequestHandler):
    def get(self):
        illustrations = Illustrations().table
        template = jinja_environment.get_template('list-illustrations.html')
        self.response.out.write(template.render(illustrations=illustrations))        


class Spreadsheet_index():
    """Read a published google spreadsheet into a list of dicts.
       Each dict is a row of the spreadsheet.
       The list is then available as the table attribute."""
    def __init__(self, google_spreadsheet_key):
        """google_spreadsheet_key is the key of the spreadsheet (can be read from the url)."""
        self._google_spreadsheet_key = google_spreadsheet_key
        self.table = []
        self.client = SpreadsheetsClient()
        self.client.client_login(
            google_credentials.USERNAME,
            google_credentials.PASSWORD,
            'catholicmissale'
        )
        self.sync_table()

    def sync_table(self):
        self.rows = self.client.get_list_feed(
            self._google_spreadsheet_key,
            google_spreadsheet_first_worksheet_id
        ).entry
        for row in self.rows:
            self.table.append(row.to_dict())

    def update_fields(self, updates, id_name='id'):
        """
        @param id_name: the name of the field by which the rows can be queried
        @param updates: a dict of dicts. The index is the value of the id_name field. Each dict contains the fields of
        a row that must be updated.
        @return: nothing
        """
        for entry in self.rows:
            id = entry.get_value(id_name)
            if id in updates:
                entry.from_dict(updates[id])
                self.client.update(entry)
                logging.info('On index updated row with ' + id_name + '=' + id)
        self.sync_table()

    def add_rows(self, additions):
        """
        @param additions: a dict of dicts. Each dict contains the fields of a row that must be added.
        @return:
        """
        for id in additions:
            additions[id]['id'] = id  # to make sure this field is also filled in if it wasn't explicitly in the dict!
            entry = ListEntry()
            entry.from_dict(additions[id])
            self.client.add_list_entry(
                entry,
                self._google_spreadsheet_key,
                google_spreadsheet_first_worksheet_id
            )
            logging.info('On index added row ' + pprint.pprint(additions[id]))
        self.sync_table()


class Illustrations(Spreadsheet_index):
    """Read the published google spreadsheet containing illustration metadata
    into a list of dicts"""
    def __init__(self):
        super(Illustrations,self).__init__(self, google_spreadsheet_missale_illustrations_key)

    def update_fields(self, updates):
        super(Illustrations,self).update_fields(updates,'id')