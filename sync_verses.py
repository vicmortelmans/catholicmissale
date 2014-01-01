import webapp2
import datastore_index
import httplib2
import httplib
import urllib
import json
import logging

logging.basicConfig(level=logging.INFO)
httplib2.Http(timeout=60)


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
        for verse in missing_verses[:]:  # taking copy of list, as items may be deleted while iterating
            yql = 'use "https://raw.github.com/vicmortelmans/yql-tables/master/bible/bible.bible.xml" as bible.bible; '\
                'select * from bible.bible where language="{lang}" and bibleref="{bibleref}";'\
                .format(lang=verse['lang'], bibleref=verse['ref'])
            url = 'http://query.yahooapis.com/v1/public/yql?q={yql}&format=json&callback='\
                .format(yql=urllib.quote(yql))
            logging.info("REST call to " + url + " (" + yql + ")")
            try:
                resp, content = httplib2.Http().request(url)
                if resp.status != 200:
                    raise YQLException("Http response " + str(resp.status))
                content = json.loads(content)
                if 'error' in content:
                    raise YQLException("YQL error " + content['error']['description'])
                if not 'query' in content:
                    raise YQLException("YQL unknown error, no query.")
                if not 'results' in content['query']:
                    raise YQLException("YQL unknown error, no results.")
                if not 'passage' in content['query']['results']:
                    raise YQLException("YQL unknown error, no passage.")
                passage = content['query']['results']['passage']
                if len(passage) == 0:
                    raise YQLException("YQL unknown error, empty passage.")
                verse['string'] = passage
            except YQLException as e:
                missing_verses.remove(verse)  # will be picked up again in the next run
                logging.info(e.value)
            except httplib.HTTPException as e:
                missing_verses.remove(verse)  # will be picked up again in the next run
                logging.info(e.message)

        # copy the missing verses into the datastore
        datastore_verses_mgr.bulkload_table(missing_verses)

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
                for lang in datastore_index.LANGUAGES:
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

