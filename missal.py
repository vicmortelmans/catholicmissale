import webapp2
import logging
import datastore_index
import lib
import model
import datetime
import zlib
import re
import urllib
from jinja_templates import jinja_environment

logging.basicConfig(level=logging.INFO)


class MissalHandler(webapp2.RequestHandler):
    def get(self, lang='en'):
        """
        @param lang: language
        @return: returns an XML file containing all masses
        """
        # query the cache
        cache = model.Missal_cache.get_or_insert(lang)
        if cache.date == datetime.date.today():
            content = zlib.decompress(cache.content).decode('unicode_escape')
        else:
            # get the datastore
            datastore_masses_mgr = datastore_index.Masses()
            masses = datastore_masses_mgr.sync_lookup_table()
#            # remove feasts that are the same in cycle B and C
#            for id in masses.keys():
#                if 'duplicate' in masses[id] and masses[id]['duplicate']:
#                    del masses[id]
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
                fixed_date=fixed_date,
                xstr=lambda s: s or ""
            )
            # update cache
            cache.content = zlib.compress(content.encode('unicode_escape'))
            cache.date = datetime.date.today()
            cache.put()
        self.response.headers['Content-Type'] = "application/xml"
        self.response.out.write(content)
        return


class QueryIllustrationsHandler(webapp2.RequestHandler):
    def get(self, lang='en', references=''):
        # get the biblerefs datastore in a lookup table
        datastore_biblerefs_mgr = datastore_index.Biblerefs()
        biblerefs = datastore_biblerefs_mgr.sync_lookup_table()
        # get the illustrations datastore in a table
        datastore_illustrations_mgr = datastore_index.Illustrations()
        illustrations = datastore_illustrations_mgr.sync_table()  # no lookup table!
        # get the verses datastore in a lookup table
        datastore_verses_mgr = datastore_index.Verses()
        verses = datastore_verses_mgr.sync_lookup_table()
        # create a dict for looking up illustrations by passageReference
        lookup_illustrations = {}  # dict by passageReference of lists of illustrations
        for i in illustrations:
            passageReference = i['passageReference']
            if passageReference not in lookup_illustrations:
                lookup_illustrations[passageReference] = []
            lookup_illustrations[passageReference].append(i)
        template = jinja_environment.get_template('illustrations.xml')
        content = template.render(
            lang=lang,
            references=references.replace('+', ' ').split('|'),
            biblerefs=biblerefs,  # list of dicts
            lookup_illustrations=lookup_illustrations,  # dict by passageReference of lists of dicts
            verses=verses,  # list of dicts
            readable_date=lib.readable_date,
            xstr=lambda s: s or ""
        )
        self.response.headers['Content-Type'] = "application/xml"
        self.response.out.write(content)
        return


class PrintHandler(webapp2.RequestHandler):
    def get(self, lang='en'):
        datastore_pagecount_mgr = datastore_index.Pagecount()
        pagecount = datastore_pagecount_mgr.sync_table()  # no lookup table!
        selected_pagecount = []
        for i in pagecount:
            edition = i['edition']
            e = edition.split('-')
            edition_language = e[-1]
            if edition_language == lang:
                i['language'] = edition_language
                i['edition_only'] = '-'.join(e[0:-1])
                selected_pagecount.append(i)
        template = jinja_environment.get_template('print.html')
        content = template.render(
            lang=lang,
            pagecount=selected_pagecount,
            languages=datastore_index.LANGUAGES['of'],  # TODO language lists for of and eo *may* deviate
            translate=model.I18n.translate,
            locales=datastore_index.LOCALES,
            quote=urllib.quote
        )
        self.response.out.write(content)
        return

class PrintBookHandler(webapp2.RequestHandler):
    def get(self, lang='en', edition_only=''):
        datastore_pagecount_mgr = datastore_index.Pagecount()
        pagecount = datastore_pagecount_mgr.sync_table()  # no lookup table!
        for i in pagecount:
            e = i['edition'].split('-')
            e_lang = e[-1]
            e_only = '-'.join(e[0:-1])
            if e_lang == lang and e_only == edition_only:
                i['language'] = lang
                i['edition_only'] = edition_only
                selected_pagecount = i
                break
        template = jinja_environment.get_template('book.html')
        content = template.render(
            lang=lang,
            e=selected_pagecount,
            languages=datastore_index.LANGUAGES['of'],  # TODO language lists for of and eo *may* deviate
            translate=model.I18n.translate,
            locales=datastore_index.LOCALES,
            quote=urllib.quote
        )
        self.response.out.write(content)
        return



def fixed_date(coordinates):
    if re.match('Z', coordinates):
        return "2000-%s-%s" % (coordinates[1:3], coordinates[3:5])
    else:
        return None