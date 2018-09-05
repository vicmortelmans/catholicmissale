import logging
from google.appengine.api import urlfetch
from google.appengine.api.urlfetch_errors import DownloadError
from google.appengine.api import blobstore
from google.appengine.api import images
from google.appengine.api import app_identity
import httplib
import os
import cloudstorage as gcs
import mimetypes


logging.basicConfig(level=logging.INFO)


bucket = '/' + os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())


class DownloadException(Exception):
    pass


class Folder():
    """Read a GCS folder into a list of dicts.
       Each dict is a file in the folder and contains fields for id and filename ('title').
       The list is then available as the table attribute."""       
    def __init__(self, path, oauth_decorator=None):
        """path is the path of the folder within the default bucky. Without '/' at beginning and end. """
        self._path = path
        self.table_only_ids = []
        #self.sync_table()

    def fetch_metadata(self, ids):
        m = {}
        for id in ids:
            m[id] = {
                'title': self.table_only_ids[id]['id'],
                'fileExtension': os.path.splitext(self.sync_table_only_ids[id]['id'])[1]
            }
        return m

    def sync_table_only_ids(self):
        del self.table_only_ids[:]  # table = [] would break the references!
        stats = gcs.listbucket('%s/%s' % (bucket, self._path))
        for stat in stats:
            id = stat.filename
            self.table_only_ids.append({'id': id})
        return self.table_only_ids


class Illustrations(Folder):
    """Read the GCS folder containing illustrations
    into a list of dicts"""
    def __init__(self, **kwargs):
        Folder.__init__(
            self,
            'illustrations',
            **kwargs
        )

    def download_images(self, images_for_download):
        """
        @param images_for_download: dict by url of {'url':..., 'caption':..., '...':...}
        @return: dict by url of {'id':..., 'url':..., etc...}
        The filename is arbitrarily based on the url
        """
        d = {}
        for url in images_for_download:
            try:
                d[url] = images_for_download[url]
                filename = images_for_download[url]['filename']
                result = urlfetch.fetch(url)
                if result.status_code != 200:
                    raise DownloadException("status code != 200")
                content_type = result.headers['content-type']
                if content_type.find("image/") == -1:
                    raise DownloadException("content type not containing 'image/'")
                file_extension = mimetypes.guess_extension(content_type)
                gcs_file_name = '%s/%s/%s%s' % (bucket, self._path, filename, file_extension)
                logging.debug("download_images() downloaded {}".format(url))
                with gcs.open(gcs_file_name, 'w', content_type=content_type,
                              options={b'x-goog-acl': b'public-read'}) as f:
                    f.write(result.content)
                logging.debug("download_images() uploaded {}".format(gcs_file_name))
                public_url = images.get_serving_url(blobstore.create_gs_key('/gs' + gcs_file_name))
                logging.debug("download_images() published {}".format(public_url))
                d[url].update({
                    'id': gcs_file_name,
                    'url': public_url,
                    'fileExtension': file_extension,
                    'filename': '%s%s' % (filename, file_extension)
                })
            except TypeError:
                d[url].update({
                    'wasted': 'TRUE'
                })
                logging.error("Could not compose filename successfully due to TypeError (image is uploaded!): %s" % url)
            except images.TransformationError:
                d[url].update({
                    'wasted': 'TRUE'
                })
                logging.error("Could not upload to Google Cloud Storage because of TransformationError: %s" % url)
            except DownloadException as e:
                d[url].update({
                    'wasted': 'TRUE'
                })
                logging.error("Could not fetch because {} [{}]".format(e.message, url))
            except httplib.HTTPException as e:
                logging.info("Upload failed: " + e.message)
        return d