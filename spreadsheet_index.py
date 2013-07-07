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


# list of row names that will be renamed by the API
renamed_columns = [
    {
        'original_name': 'fileExtension',
        'short_name': 'fileextension'
    }
]


def short_names(d):
    """
    @param d: dict containing fields of a row in the spreadsheet
    @return: same dict, but with the row names as they are in the API (lower case, no spaces, underscores, etc)
    """
    for c in renamed_columns:
        d[c['short_name']] = d.pop(c['original_name'])
    return d


def original_names(d):
    """
    @param d: dict containing fields of a row in the spreadsheet as they are in the API
    @return: same dict, but with the original row names
    """
    for c in renamed_columns:
        d[c['original_name']] = d.pop(c['short_name'])
    return d


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
        self._client = SpreadsheetsClient()
        self._client.client_login(
            google_credentials.USERNAME,
            google_credentials.PASSWORD,
            'catholicmissale'
        )
        self.sync_table()

    def sync_table(self):
        self.table = []
        self._rows = self._client.get_list_feed(
            self._google_spreadsheet_key,
            google_spreadsheet_first_worksheet_id
        ).entry
        for row in self._rows:
            self.table.append(original_names(row.to_dict()))

    def update_fields(self, updates, id_name):
        """
        @param id_name: the name of the field by which the rows can be queried
        @param updates: a dict of dicts. The index is the value of the id_name field. Each dict contains the fields of
        a row that must be updated.
        @return: nothing
        """
        for entry in self._rows:
            id = entry.get_value(id_name)
            if id in updates:
                entry.from_dict(short_names(updates[id]))
                self._client.update(entry)
                logging.info('On index updated row with ' + id_name + '=' + id)
        if updates:
            self.sync_table()

    def add_rows(self, additions):
        """
        @param additions: a dict of dicts. Each dict contains the fields of a row that must be added.
        @return:
        """
        for id in additions:
            additions[id]['id'] = id  # to make sure this field is also filled in if it wasn't explicitly in the dict!
            entry = ListEntry()
            entry.from_dict(short_names(additions[id]))
            self._client.add_list_entry(
                entry,
                self._google_spreadsheet_key,
                google_spreadsheet_first_worksheet_id
            )
            logging.info('On index added row ' + pprint.pprint(additions[id]))
        if additions:
            self.sync_table()

    def delete_rows(self, obsolete_rows, id_name):
        for entry in self._rows:
            id = entry.get_value(id_name)
            if id in obsolete_rows:
                self._client.delete(entry)
                logging.info('On index deleted row with ' + id_name + '=' + id)
        if obsolete_rows:
            self.sync_table()


class Illustrations(Spreadsheet_index):
    """Read the published google spreadsheet containing illustration metadata
    into a list of dicts"""
    def __init__(self):
        Spreadsheet_index.__init__(self, google_spreadsheet_missale_illustrations_key)

    def update_fields(self, updates):
        Spreadsheet_index.update_fields(self, updates, 'id')

    def delete_rows(self, obsolete_rows):
        Spreadsheet_index.delete_rows(self, obsolete_rows, 'id')