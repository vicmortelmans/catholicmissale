import webapp2
import logging
import datastore_index
import lib
import model
import datetime
import zlib
from jinja_templates import jinja_environment

logging.basicConfig(level=logging.INFO)


class MissalHandler(webapp2.RequestHandler):
    def get(self, lang='en'):
        # query the cache
        cache = model.Missal_cache.get_or_insert(lang)
        if cache.date == datetime.date.today():
            content = zlib.decompress(cache.content).decode('unicode_escape')
        else:
            # get the datastore
            datastore_masses_mgr = datastore_index.Masses()
            masses = datastore_masses_mgr.sync_lookup_table()
            datastore_i18n_mgr = datastore_index.I18n()
            i18n = datastore_i18n_mgr.sync_lookup_table()
            datastore_biblerefs_mgr = datastore_index.Biblerefs()
            biblerefs = datastore_biblerefs_mgr.sync_lookup_table()
            datastore_illustrations_mgr = datastore_index.Illustrations()
            illustrations = datastore_illustrations_mgr.sync_table()  # no lookup table!
            datastore_verses_mgr = datastore_index.Verses()
            verses = datastore_verses_mgr.sync_lookup_table()
            # create a dict for looking up illustrations by passageReference
            lookup_illustrations = {}  # dict by passageReference of lists of illustrations
            for i in illustrations:
                passageReference = i['passageReference']
                if passageReference not in lookup_illustrations:
                    lookup_illustrations[passageReference] = []
                lookup_illustrations[passageReference].append(i)
            template = jinja_environment.get_template('missal.xml')
            content = template.render(
                lang=lang,
                masses=masses,  # list of dicts
                i18n=i18n,  # list of dicts
                biblerefs=biblerefs,  # list of dicts
                lookup_illustrations=lookup_illustrations,  # dict by passageReference of lists of dicts
                verses=verses,  # list of dicts
                readable_date=lib.readable_date,
                xstr=lambda s: s or ""
            )
            # update cache
            cache.content = zlib.compress(content.encode('unicode_escape'))
            cache.date = datetime.date.today()
            cache.put()
        self.response.headers['Content-Type'] = "application/xml"
        self.response.out.write(content)
        return
