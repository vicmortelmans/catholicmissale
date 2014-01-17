from oauth2_three_legged import Oauth2_service
import logging
import re
from google.appengine.api.urlfetch_errors import DownloadError
import urllib
import httplib
import io
from apiclient.http import MediaIoBaseUpload
from lib import slugify
import google_credentials


logging.basicConfig(level=logging.INFO)

API_CLIENT = 'drive'
VERSION = 'v2'
OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'

if google_credentials.DEV:
    google_drive_missale_images_folder_id = '0B-659FdpCliwQ1RldHZ6XzlJUEk'
else:
    google_drive_missale_images_folder_id = '0B-659FdpCliwWWJrSVRfSU5oVHc'


class Folder():
    """Read a Google Drive folder into a list of dicts.
       Each dict is a file in the folder and contains fields for id and filename ('title').
       The list is then available as the table attribute."""       
    def __init__(self, google_drive_folder_id):
        """google_drive_folder_id is the id of the folder (can be read from the url)."""
        self._google_drive_folder_id = google_drive_folder_id
        self._drive_service = Oauth2_service(API_CLIENT, VERSION, OAUTH_SCOPE).service
        self.table_only_ids = []
        #self.sync_table()

    def fetch_metadata(self, ids):
        m = {}
        for id in ids:
            try:
                metadata = self._drive_service.files().get(fileId=id).execute()
                if 'fileExtension' in metadata and re.match('jpg|JPG|jpeg|JPEG|png|PNG', metadata['fileExtension']):
                    m[id] = {
                        'title': metadata['title'],
                        'fileExtension': metadata['fileExtension']
                    }
            except DownloadError:
                logging.warning('On drive, failed to get metadata for file with id = ' + id)
            except Exception, error:
                logging.warning('On drive, an http error occurred: %s' % error)
        return m

    def sync_table_only_ids(self):
        del self.table_only_ids[:]  # table = [] would break the references!
        # the default maxResults is 100, so a loop is required
        page_token = None
        while True:
            param = {}
            if page_token:
                param['pageToken'] = page_token
            files = self._drive_service.children().list(
                folderId=self._google_drive_folder_id,
                q='trashed = false',
                **param
            ).execute()
            for f in files.get('items', []):
                id = f['id']
                self.table_only_ids.append({'id': id})
            page_token = files.get('nextPageToken')
            if not page_token:
                break
        return self.table_only_ids

    def rename_files(self, new_names):
        """
        @param new_names: a fileId-indexed dict of dicts containing 'filename'
        @return:
        """
        for id in new_names:
            try:
                metadata = self._drive_service.files().get(fileId=id).execute()
                old_name = metadata['title']
                new_name = new_names[id]['filename']
                metadata['title'] = new_name
                self._drive_service.files().update(fileId=id, body=metadata).execute()
                logging.info("On drive, renamed " + old_name + ' to ' + new_name)
            except DownloadError:
                logging.warning('On drive, failed to update metadata for file with id = ' + id)
            except Exception, error:
                logging.warning('On drive, an http error occurred: %s' % error)


class Illustrations(Folder):
    """Read the Google Drive folder containing illustrations
    into a list of dicts"""
    def __init__(self):
        Folder.__init__(self, google_drive_missale_images_folder_id)

    def download_images(self, images_for_download):
        """
        @param images_for_download: dict by url of {'url':...}
        @return: dict by url of {'id':..., 'url':...}
        The filename is arbitrarily based on the url
        """
        d = {}
        for url in images_for_download:
            try:
                filename = slugify(url)
                file = urllib.urlopen(url)
                fd = io.BytesIO(file.read())
                media = MediaIoBaseUpload(fd, mimetype='image/png', chunksize=1024*1024, resumable=True)
                metadata = {
                    'title': filename,
                    'parents': [
                        {
                            'id': google_drive_missale_images_folder_id
                        }
                    ]
                }
                request = self._drive_service.files().insert(media_body=media, body=metadata)
                response = None
                while response is None:
                  status, response = request.next_chunk()
                  if status:
                    logging.info("Uploaded %d%%." % int(status.progress() * 100))
                logging.info("Upload Complete!")
                id = response['id']
                fileExtension = response['fileExtension']
                d[url] = {'id': id, 'url': url, 'fileExtension': fileExtension}
            except httplib.HTTPException as e:
                logging.info("Upload failed: " + e.message)
        return d