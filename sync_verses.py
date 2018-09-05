import webapp2
import datastore_index
import urllib2
import httplib
import urllib
import json
import logging
import lib

logging.basicConfig(level=logging.INFO)


class YQLException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class SyncVersesHandler(webapp2.RequestHandler):
    def get(self):

        # get the contents of the biblerefs datastore
        datastore_biblerefs_mgr = datastore_index.Biblerefs()
        self.datastore_biblerefs = datastore_biblerefs_mgr.sync_table()

        # get the contents of the verses datastore
        datastore_verses_mgr = datastore_index.Verses()
        self.datastore_verses = datastore_verses_mgr.sync_table()

        # get the contents of the illustrations datastore
        datastore_illustrations_mgr = datastore_index.Illustrations()
        self.datastore_illustrations = datastore_illustrations_mgr.sync_table()

        # dict by id of verse dicts {
        missing_verses = []
        self.find_missing_verses(missing_verses)

        # fetch missing verses from online sources
        missing_verses_chunks = lib.chunks(missing_verses, 25)
        for missing_verses_chunk in missing_verses_chunks:
            for verse in missing_verses_chunk[:]:  # taking copy of list, as items may be deleted while iterating
                url = "http://catecheserooster.appspot.com/yql/bible?bibleref={reference}&language={language}&tolerance=true" \
                    .format(
                        language=verse['lang'],
                        reference=urllib.quote(verse['ref'].encode('utf8'))
                    )
                logging.info("REST call to " + url)
                try:
                    content = json.loads(urllib2.urlopen(url).read())
                    if not content:
                        raise YQLException("Http response ")
                    passage = content['passage']
                    if len(passage) == 0 or passage == '.':
                        raise YQLException("Bible API unknown error, empty passage.")
                    verse['string'] = passage
                    if not 'bibleref' in content:
                        raise YQLException("YQL unknown error, no local bibleref.")
                    if len(passage) == 0 or passage == '.':
                        verse['local_ref'] = verse['ref']
                    else:
                        verse['local_ref'] = content['bibleref']
                except YQLException as e:
                    missing_verses_chunk.remove(verse)  # will be picked up again in the next run
                    logging.log(logging.ERROR, "Dropping verse in " + verse['lang'] + " with ref=" + verse['ref'] + " because " + e.value)
                except httplib.HTTPException as e:
                    missing_verses_chunk.remove(verse)  # will be picked up again in the next run
                    logging.log(logging.ERROR, "Dropping verse in " + verse['lang'] + " with ref=" + verse['ref'] + " because " + e.message)

            # copy the missing verses into the datastore
            datastore_verses_mgr.bulkload_table(missing_verses_chunk)

        # find obsolete datastore entities (not in biblerefs)
        obsolete_entities = {}
        self.find_obsolete_entities(obsolete_entities)

        # delete the obsolete datastore entities
        datastore_verses_mgr.delete_entities(obsolete_entities)

        # the app redirects the user to the index
        self.response.out.write("Verses datastore updated")


    def find_missing_verses(self, d):
        """
        @param d: list of dicts to be filled in
        @return: list of dicts filled in with 'id', 'ref' and 'lang' for missing verses
        """
        illustration_biblerefs = [i['passageReference'] for i in self.datastore_illustrations]
        verses_ids = [i['id'] for i in self.datastore_verses]
        for i in self.datastore_biblerefs:
            bibleref = i['reference']
            if bibleref in illustration_biblerefs:
                for lang in datastore_index.ALL_LANGUAGES:
                    id = lang + '.' + bibleref
                    if id not in verses_ids:
                        verse = {
                            'id': id,
                            'ref': bibleref,
                            'lang': lang
                        }
                        d.append(verse)

    def find_obsolete_entities(self, d):
        biblerefs = [i['reference'] for i in self.datastore_biblerefs]
        for i in self.datastore_verses:
            bibleref = i['ref']
            if bibleref not in biblerefs:
                id = i['id']
                d[id] = {}


