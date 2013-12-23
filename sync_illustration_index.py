import webapp2
from jinja_templates import jinja_environment
import drive_index
import spreadsheet_index
import datastore_index
import re
from lib import slugify

GOOGLE_DRIVE_HOST_PREFIX = "https://googledrive.com/host/" + drive_index.google_drive_missale_images_folder_id


class SyncIllustrationHandler(webapp2.RequestHandler):
    def get(self):
        # get the contents of the index spreadsheet
        index_illustrations_mgr = spreadsheet_index.Illustrations()
        self.index_illustrations = index_illustrations_mgr.sync_table()

        # see if there have been image URLs submitted to the spreadsheet index for downloading
        # (they can be recognized because they don't have a drive ID yet)
        images_for_download = {}  # dict by url (!) of dicts containing 'url'
        self.find_images_for_download(images_for_download)

        # download the images and collect the id's in a dict by url of dicts containing 'id'
        drive_illustration_mgr = drive_index.Illustrations()
        downloaded_images = drive_illustration_mgr.download_images(images_for_download)

        # update the spreadsheet index entries with the new id's
        index_illustrations_mgr.update_fields_by_url(downloaded_images)

        # get the contents of the drive folder
        self.drive_illustrations = drive_illustration_mgr.sync_table()

        # find new images in the drive folder by comparing the id fields
        # the file title is the initial caption
        new_images = {}  # dict by id of dicts containing 'caption', 'filename' and 'url'
        self.find_new_images(new_images)

        # add the rows for the update list entries
        index_illustrations_mgr.add_rows(new_images)

        # find obsolete spreadsheet index entries (no id or no drive image with same id)
        obsolete_index_rows = {}  # dict by id of dicts containing 'wasted'
        self.find_obsolete_index_rows(obsolete_index_rows)

        # mark the obsolete spreadsheet index enries as wasted
        index_illustrations_mgr.update_fields(obsolete_index_rows)

        # compose a caption for each entry in the index spreadsheet based on the fields in the index, unless all
        # fields are empty, then check if the URL is empty, and if so, just copy the original caption
        update_captions = {}  # dict by id of dicts containing 'caption', 'filename' and 'url'
        self.compose_captions(update_captions)

        # compose a filename and url (= lower-case dash-separated caption; important for SEO!) for each entry in the
        # update list
        self.compose_filenames(update_captions)

        # update the rows for the update list entries
        index_illustrations_mgr.update_fields(update_captions)

        # find images in the drive folder with non-matching filename
        renamed_images = {}
        self.find_renamed_images(renamed_images)

        # rename the files on Drive
        drive_illustration_mgr.rename_files(renamed_images)

        # setup the datastore
        datastore_illustrations_mgr = datastore_index.Illustrations()

        # copy the data in the index to the datastore
        # get the rows for which biblerefs are updated during registration
        updated_index_rows = datastore_illustrations_mgr.bulkload_table(self.index_illustrations)

        # update the rows for the update list entries
        index_illustrations_mgr.update_fields(updated_index_rows)

        # load the datastore
        self.datastore_illustrations = datastore_illustrations_mgr.sync_table()

        # find obsolete datastore entities (no drive file with same id or wasted)
        obsolete_entities = {}
        self.find_obsolete_entities(obsolete_entities)

        # delete the obsolete datastore entities
        datastore_illustrations_mgr.delete_entities(obsolete_entities)

        # the app redirects the user to the index
        template = jinja_environment.get_template('list-illustrations.html')
        self.response.out.write(template.render(illustrations=self.datastore_illustrations))

    def find_images_for_download(self, d):
        """
        @param d: an emtpy dict
        @return: the dict filled with rows from the spreadsheet index
        that had an url but no id
        """
        for i in self.index_illustrations:
            if not i['id'] and i['url']:
                d[i['url']] = {'url': i['url']}

    def compose_captions(self, d):
        """ compose a (non-empty) caption for each spreadsheet index entry and store it in update_captions """
        for i in self.index_illustrations:
            id = i['id'] or random_id()  # rows that are entered by the syncer should always have an id !
            caption = compose_caption(
                title=i['title'],
                artist=i['artist'],
                year=i['year'],
                location=i['location'],
                copyright=i['copyright']
            )
            fileExtension = i['fileExtension']
            if caption != ' ':  # result of all empty metadata fields
                d[id] = {'caption': caption, 'fileExtension': fileExtension}
            elif not i['url']:
                d[id] = {'caption': i['caption'], 'fileExtension': fileExtension}

    def ignore_unchanged_or_unknown_captions(self, d):
        """ only keep  the entries that have a matching drive entry (by id) and that have a
            generated caption not matching the stored caption (e.g. the user has updated the
            title in the spreadsheet) """
        keep = []
        for i in self.index_illustrations:
            id = i['id']
            if id in d and d[id]['caption'] != i['caption']:
                keep.append(id)
        # an easier construct is imaginable, but I cannot reassign 'd = ...'
        ignore = [id for id in d if id not in keep]
        for id in ignore:
            del d[id]

    def compose_filenames(self, d):
        for id in d:
            caption = d[id]['caption']
            fileExtension = d[id]['fileExtension'] or ""
            fileExtension = fileExtension if fileExtension is not None else ''
            filename = slugify(caption) + '.' + fileExtension
            url = GOOGLE_DRIVE_HOST_PREFIX + '/' + filename
            d[id]['filename'] = filename
            d[id]['url'] = url

    def find_new_images(self, d):
        # find images in drive that are not in index (by id)
        index_ids = [i['id'] for i in self.index_illustrations]
        for i in self.drive_illustrations:
            id = i['id']
            if id not in index_ids:
                d[id] = {'caption': i['title'], 'fileExtension': i['fileExtension']}

    def find_renamed_images(self, d):
        # find images in drive that have a title not matching the filename in the index
        # store the index-filename in d
        index_filenames = {i['id']: i['filename'] for i in self.index_illustrations}
        for i in self.drive_illustrations:
            id = i['id']
            if id in index_filenames and index_filenames[id] != i['title']:
                d[id] = {'filename': index_filenames[id]}

    def find_obsolete_index_rows(self, d):
        drive_ids = [i['id'] for i in self.drive_illustrations]
        for i in self.index_illustrations:
            id = i['id']
            if id not in drive_ids:
                d[id] = {'wasted': "True"}

    def find_obsolete_entities(self, d):
        drive_ids = [i['id'] for i in self.drive_illustrations]
        for i in self.datastore_illustrations:
            id = i['id']
            if id not in drive_ids or i['wasted']:
                d[id] = {}


def compose_caption(title=None, artist=None, year=None, location=None, copyright=None):
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