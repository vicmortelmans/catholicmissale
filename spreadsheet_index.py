import webapp2
from jinja_templates import jinja_environment
from gdata.spreadsheets.client import SpreadsheetsClient
from gdata.spreadsheets.data import ListEntry
import google_credentials
# USERNAME = ''
# PASSWORD = ''
import logging

logging.basicConfig(level=logging.INFO)

google_spreadsheet_missale_illustrations_key = "0Au659FdpCliwdEtYWm81eEMwUGQ1RlMybUx2UU5BLXc"
google_spreadsheet_first_worksheet_id = 'od6'
google_spreadsheet_missale_masses_key = "0Au659FdpCliwdEdOUElBaUVXSFRoY0dCbHowWGM4VEE"
google_spreadsheet_missale_masses_worksheet_id = 'od4'

reading_references_separator = '|'

# list of column names that will be renamed by the API
renamed_columns = [
    {
        'original_name': 'fileExtension',
        'short_name': 'fileextension'
    },
    {
        'original_name': 'oldUrl',
        'short_name': 'oldurl'
    },
    {
        'original_name': 'passageReference',
        'short_name': 'passagereference'
    }
]

# list of column names that contain repeated properties represented as joined strings
repeated_properties = [
    {
        'name': 'cycle',
        'separator': ''
    },
    {
        'name': 'gospel',
        'separator': reading_references_separator
    },
    {
        'name': 'lecture',
        'separator': reading_references_separator
    },
    {
        'name': 'epistle',
        'separator': reading_references_separator
    }
]

# list of columnnames that contain integer ata
integer_properties = [
    {
        'name': 'order'
    }
]


def export_for_spreadsheet(d):
    """
    @param d: dict containing fields of a row in the spreadsheet
    @return: same dict, but with the row names as they are in the API (lower case, no spaces, underscores, etc)
    and the lists of the repeating properties joined into a string
    and the integer values casted to integer variables
    all of this to align the dict better to the corresponding entity in model.py
    and to be able to call setattr() without getting type errors
    but beware that this conversion will cause trouble if different spreadsheets use the same column names
    for different type of fields!!
    """
    for c in renamed_columns:
        if c['original_name'] in d:
            d[c['short_name']] = d.pop(c['original_name'])
    for c in repeated_properties:
        if c['name'] in d:
            if d[c['name']]:
                d[c['name']] = c['separator'].join(d[c['name']])
            else:
                d[c['name']] = ''
    for c in integer_properties:
        if c['name'] in d:
            if d[c['name']]:
                d[c['name']] = str(d[c['name']])
            else:
                d[c['name']] = ''
    return d


def import_from_spreadsheet(d):
    """
    @param d: dict containing fields of a row in the spreadsheet as they are in the API
    @return: same dict, but with the original row names
    and the strings of the repeating properties split into lists
    """
    for c in renamed_columns:
        if c['short_name'] in d:
            d[c['original_name']] = d.pop(c['short_name'])
    for c in repeated_properties:
        if c['name'] in d:
            if d[c['name']]:
                if c['separator']:
                    d[c['name']] = d[c['name']].split(c['separator'])
                else:
                    d[c['name']] = list(d[c['name']])  # split into characters
            else:
                d[c['name']] = []
    for c in integer_properties:
        if c['name'] in d:
            if d[c['name']]:
                d[c['name']] = int(d[c['name']])
    return d


class ListSpreadsheetHandler(webapp2.RequestHandler):
    def get(self):
        illustrations = Illustrations().table
        template = jinja_environment.get_template('list-illustrations.html')
        self.response.out.write(template.render(illustrations=illustrations))        


class Spreadsheet_index():
    """Read a published google spreadsheet into a list of dicts.
       Each dict is a row of the spreadsheet.
       Repeated properties are represented as a list.
       The list is then available as the table attribute."""
    def __init__(self, google_spreadsheet_key,google_worksheet_id):
        """google_spreadsheet_key is the key of the spreadsheet (can be read from the url)."""
        self._google_spreadsheet_key = google_spreadsheet_key
        self._google_worksheet_id = google_worksheet_id
        self._client = SpreadsheetsClient()
        self._client.client_login(
            google_credentials.USERNAME,
            google_credentials.PASSWORD,
            'catholicmissale'
        )
        self.table = []
        self.sync_table()

    def sync_table(self):
        del self.table[:]  # table = [] would break the references!
        self._rows = self._client.get_list_feed(
            self._google_spreadsheet_key,
            self._google_worksheet_id
        ).entry
        for row in self._rows:
            self.table.append(import_from_spreadsheet(row.to_dict()))

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
                entry.from_dict(export_for_spreadsheet(updates[id]))
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
            entry.from_dict(export_for_spreadsheet(additions[id]))
            self._client.add_list_entry(
                entry,
                self._google_spreadsheet_key,
                google_spreadsheet_first_worksheet_id
            )
            logging.info('On index added row with id = ' + id)
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
        Spreadsheet_index.__init__(
            self,
            google_spreadsheet_missale_illustrations_key,
            google_spreadsheet_first_worksheet_id
        )

    def update_fields(self, updates):
        Spreadsheet_index.update_fields(self, updates, 'id')

    def update_fields_by_url(self, updates):
        Spreadsheet_index.update_fields(self, updates, 'url')

    def delete_rows(self, obsolete_rows):
        Spreadsheet_index.delete_rows(self, obsolete_rows, 'id')


class Masses(Spreadsheet_index):
    def __init__(self):
        Spreadsheet_index.__init__(
            self,
            google_spreadsheet_missale_masses_key,
            google_spreadsheet_missale_masses_worksheet_id
        )

    def update_fields(self, updates):
        Spreadsheet_index.update_fields(self, updates, 'key')
