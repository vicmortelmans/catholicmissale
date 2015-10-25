# -*- coding: utf-8 -*-
import webapp2
from jinja_templates import jinja_environment
import drive_index
import spreadsheet_index
import datastore_index
import gcs_index
import re
import time
from lib import slugify
from main import decorator as GlobalOAuth2Decorator
import logging

logging.basicConfig(level=logging.INFO)

GOOGLE_DRIVE_HOST_PREFIX = "https://googledrive.com/host/" + drive_index.google_drive_missale_images_folder_id


class SyncIllustrationHandler(webapp2.RequestHandler):

    @GlobalOAuth2Decorator.oauth_required
    def get(self):
        # get the contents of the index spreadsheet
        # READ spreadsheet
        # WRITE memory-spreadsheet
        index_illustrations_mgr = spreadsheet_index.Illustrations(oauth_decorator=GlobalOAuth2Decorator)
        self.index_illustrations = index_illustrations_mgr.sync_table()

        # see if there have been image URLs submitted to the spreadsheet index for downloading
        # (they can be recognized because they don't have a drive ID yet)
        # this can also be image rows that have been edited (ID is deleted automatically)
        # or image rows that have the ID removed manually, for migration from Drive to GCS
        # READ memory-spreadsheet
        # WRITE variable
        images_for_download = {}  # dict by url (!) of dicts containing 'url', 'caption', 'sync', etc... (but no id)
        self.find_images_for_download(images_for_download)
        logging.info("Images for download found: {}".format(len(images_for_download)))

        # download the images and collect the id's in a dict by url of dicts containing 'id'
        # READ variable
        # WRITE Drive, GCS
        # WRITE variable
        drive_illustration_mgr = drive_index.Illustrations(oauth_decorator=GlobalOAuth2Decorator)
        gcs_illustration_mgr = gcs_index.Illustrations(oauth_decorator=GlobalOAuth2Decorator)
        downloaded_images = gcs_illustration_mgr.download_images(images_for_download)
        logging.info("Images downloaded: {}".format(len(downloaded_images)))

        # update the spreadsheet index entries with the new id's
        # READ variable
        # WRITE memory-spreadsheet
        # WRITE spreadsheet
        index_illustrations_mgr.update_fields_by_url(downloaded_images)

        # get the contents of the drive folder (no metadata yet)
        # READ drive
        # WRITE memory-drive
        self.drive_illustrations_ids = drive_illustration_mgr.sync_table_only_ids()

        # get the contents of the GCS folder (no metadata yet)
        # READ gcs
        # WRITE memory-gcs
        self.gcs_illustrations_ids = gcs_illustration_mgr.sync_table_only_ids()

        # uploading images to the GCS folder will not be supported

        # find obsolete spreadsheet index entries (no id or no drive image or no gcs image with same id)
        # READ memory-spreadsheet, memory-drive, memory-gcs
        # WRITE variable
        obsolete_index_rows = {}  # dict by id of dicts containing 'wasted'
        self.find_obsolete_index_rows(obsolete_index_rows)
        logging.info("Obsolete rows found: {}".format(len(obsolete_index_rows)))

        # mark the obsolete spreadsheet index entries as wasted
        # READ variable
        # WRITE memory-spreadsheet
        # WRITE spreadsheet
        index_illustrations_mgr.update_fields(obsolete_index_rows)

        # setup the datastore
        datastore_illustrations_mgr = datastore_index.Illustrations()

        # copy the data in the index to the datastore
        # get the rows for which biblerefs are updated during registration
        updated_index_rows = datastore_illustrations_mgr.bulkload_table(self.index_illustrations)
        logging.info("Rows with updated biblerefs found: {}".format(len(updated_index_rows)))

        # update the rows for the update list entries
        index_illustrations_mgr.update_fields(updated_index_rows)

        # load the datastore
        self.datastore_illustrations = datastore_illustrations_mgr.sync_table()

        # find obsolete datastore entities  not in index or (no drive file and no GCS file with same id or wasted)
        obsolete_entities = {}
        self.find_obsolete_entities(obsolete_entities)
        logging.info("Obsolete datastore entities found: {}".format(len(obsolete_entities)))

        # delete the obsolete datastore entities
        datastore_illustrations_mgr.delete_entities(obsolete_entities)

        # the app redirects the user to the index
        template = jinja_environment.get_template('list-illustrations.html')
        self.response.out.write(template.render(illustrations=self.datastore_illustrations))

    def find_images_for_download(self, d):
        """
        @param d: an emtpy dict
        @return: the dict (by url) filled with rows from the spreadsheet index
        that had an url but no id
        """
        sync = time.strftime('%Y-%m-%d %H:%M:%S')
        for i in self.index_illustrations:
            if not i['id'] and i['url'] and not ('wasted' in i and i['wasted']):
                caption = compose_caption(
                    title=i['title'],
                    artist=i['artist'],
                    year=i['year'],
                    location=i['location'],
                    copyright=i['copyright']
                ) or i['caption'] or slugify(i['url'])
                filename = slugify(caption)  # file extension is added later on
                d[i['url']] = {
                    'url': i['url'],
                    'caption': caption,
                    'filename': filename,
                    'sync': sync
                }
                logging.debug("find_images_for_download() found %s [%s]" % (caption, i['url']))

    def find_obsolete_index_rows(self, d):
        drive_ids = [i['id'] for i in self.drive_illustrations_ids]
        gcs_ids = [i['id'] for i in self.gcs_illustrations_ids]
        for i in self.index_illustrations:
            id = i['id']
            if not id or (id not in drive_ids and id not in gcs_ids):
                d[id] = {'wasted': "True"}
                logging.debug("find_obsolete_index_rows() found {}".format(id))

    def find_obsolete_entities(self, d):
        drive_ids = [i['id'] for i in self.drive_illustrations_ids]
        gcs_ids = [i['id'] for i in self.gcs_illustrations_ids]
        index_ids = [i['id'] for i in self.index_illustrations]
        for i in self.datastore_illustrations:
            id = i['id']
            if id not in index_ids or (id not in drive_ids and id not in gcs_ids) or ('wasted' in i and i['wasted']):
                d[id] = {}
                logging.debug("find_obsolete_entities() found {}".format(id))


def compose_caption(title=None, artist=None, year=None, location=None, copyright=None):
    if copyright:
        copyright = u"© " + copyright
    c = "%s (%s, %s, %s, %s)" % (title or '', artist or '', year or '', location or '', copyright or '')
    c = re.sub(r', , ', ', ', c)
    c = re.sub(r', , ', ', ', c)
    c = re.sub(r', , ', ', ', c)
    c = re.sub(r', \(, \)+', ', ', c)
    c = re.sub(r'\(, ', '(', c)
    c = re.sub(r', \)', ')', c)
    c = re.sub(r'\(, \)', '', c)
    c = re.sub(r'\(\)', '', c)
    return c


def random_id():
    from random import random
    return int(1000 * random())