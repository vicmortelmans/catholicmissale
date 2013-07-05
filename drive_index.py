from oauth2_three_legged import Oauth2_service
from apiclient import errors
import logging

logging.basicConfig(level=logging.INFO)

API_CLIENT = 'drive'
VERSION = 'v2'
OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'

google_drive_missale_images_folder_id = '0B-659FdpCliwOUUxQmxONnJkRlE' 


class Folder():
    """Read a Google Drive folder into a list of dicts.
       Each dict is a file in the folder and contains fields for id and filename ('title').
       The list is then available as the table attribute."""       
    def __init__(self, google_drive_folder_id):
        """google_drive_folder_id is the id of the folder (can be read from the url)."""
        self.google_drive_folder_id = google_drive_folder_id
        self.table = []
        self.drive_service = Oauth2_service(API_CLIENT, VERSION, OAUTH_SCOPE).service
        self.sync_table()

    def sync_table(self):
        files = self.drive_service.children().list(folderId=self.google_drive_folder_id).execute()
        for f in files.get('items', []):
            metadata = self.drive_service.files().get(fileId=f['id']).execute()
            self.table.append(dict((key, metadata[key]) for key in ['id', 'title', 'fileExtension']))

    def rename_files(self, new_names):
        """
        @param new_names: a fileId-indexed dict of dicts containing 'filename'
        @return:
        """
        for id in new_names:
            metadata = self.drive_service.files().get(fileId=id).execute()
            old_name = metadata['title']
            new_name = new_names[id]['filename']
            metadata['title'] = new_name
            try:
                self.drive_service.files().update(fileId=id, body=metadata).execute()
                logging.info("On drive, renamed " + old_name + ' to ' + new_name)
            except errors.HttpError, error:
                print 'An error occurred: %s' % error
        self.sync_table()


class Illustrations(Folder):
    """Read the Google Drive folder containing illustrations
    into a list of dicts"""
    def __init__(self):
        super(Illustrations,self).__init__(self, google_drive_missale_images_folder_id)