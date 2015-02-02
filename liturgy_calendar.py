import webapp2
import logging
import datastore_index
import lib
import model
import datetime
import zlib
from jinja_templates import jinja_environment
import pickle

logging.basicConfig(level=logging.INFO)


class XmlCalendarHandler(webapp2.RequestHandler):
    def get(self, form='of'):
        # query the cache
        cache = model.Calendar_cache.get_or_insert(form)
        if cache.date == datetime.date.today():
            content = zlib.decompress(cache.content).decode('unicode_escape')
        else:
            # get the datastore
            datastore_dates_mgr = datastore_index.Dates()
            dates = datastore_dates_mgr.sync_table()
            template = jinja_environment.get_template('liturgical_calendar.xml')
            content = template.render(
                form=form,
                dates=dates,  # list of dicts
                years=datastore_index.YEARS,
                languages=datastore_index.LANGUAGES,
                readable_date=lib.readable_date
            )
            # update cache
            cache.content = zlib.compress(content.encode('unicode_escape'))
            cache.date = datetime.date.today()
            cache.put()
        self.response.headers['Content-Type'] = "application/xml"
        self.response.out.write(content)
        return


class PickleCalendarHandler(webapp2.RequestHandler):
    def get(self, form='of'):
        key = 'pickle' + form
        # query the cache
        cache = model.Calendar_cache.get_or_insert(key)
        if cache.date == datetime.date.today():
            content = zlib.decompress(cache.content).decode('unicode_escape')
        else:
            # get the datastore
            datastore_dates_mgr = datastore_index.Dates()
            dates = datastore_dates_mgr.sync_table()
            languages = datastore_index.LANGUAGES
            days = []
            for date in dates:
                if date['form'] == form:
                    if not date['mass']:
                        logging.error("Error: empty 'mass' field in Date")
                        continue  # TODO this happens for eo on P022-P026 and between F067 and 24S1
                    day = {}
                    day['coordinates'] = date['mass']
                    day['date'] = date['date']
                    day['form'] = form
                    day['cycle'] = date['cycle']
                    day['rank'] = date['rank']
                    day['season'] = date['season']
                    day['color'] = date['color']
                    for lang in languages[form]:
                        i18n = model.I18n.translate_liturgical_day(form, date['mass'], lang)
                        if hasattr(i18n, 'string'):
                            day[lang] = i18n.string
                        else:
                            day[lang] = ''  # should only be needed when debugging
                    days.append(day)
            content = pickle.dumps(days)
            # update cache
            cache.content = content
            cache.date = datetime.date.today()
            cache.put()

        # feedback to the user
        self.response.out.write("Dates pickled and cached in datastore")
        return


class ICalendarHandler(webapp2.RedirectHandler):
    def get(self, scope=None, form='of', lang='en'):
        ical_key = 'ical' + scope + form + lang
        # query the cache
        cache = model.Calendar_cache.get_or_insert(ical_key)
        if cache.content:
            content = zlib.decompress(cache.content).decode('unicode_escape')
            logging.info("Got ical calendar %s from cache." % ical_key)
        else:
            pickle_key = 'pickle' + form
            # this service will NOT refresh the data, but rely only on the cache !
            pickle_cache = model.Calendar_cache.get_or_insert(pickle_key)
            if not pickle_cache.content:
                logging.error("First sync-i18n-of, sync-i18n-eo and sync-date is needed!")
                raise webapp2.abort(404)
            logging.info("Got pickled calendar %s from cache." % ical_key)
            pickle_content = pickle_cache.content
            days = pickle.loads(pickle_content)
            if scope == 'sundays-and-feasts':
                name_i18n = model.I18n.translate('liturgical-calendar-for-sundays-and-feasts', lang)
            else:  # scope == 'weekdays'
                name_i18n = model.I18n.translate('liturgical-calendar-for-weekdays', lang)
            if hasattr(name_i18n, 'string'):
                name = name_i18n.string
            else:
                name = "missale.net"
            if form == 'of':
                form_i18n = model.I18n.translate('ordinary-form', lang)
            else:  # form == 'eo'
                form_i18n = model.I18n.translate('extraordinary-form', lang)
            if hasattr(form_i18n, 'string'):
                name += " (%s)" % form_i18n.string
            template = jinja_environment.get_template('liturgical-calendar.ics')
            content = template.render(
                scope=scope,
                form=form,
                lang=lang,
                name=name,
                days=days,  # list of dicts
            ).replace('\n', '\r\n')
            logging.info("Generated ical calendar %s." % ical_key)
            # update cache
            cache.content = zlib.compress(content.encode('unicode_escape'))
            cache.put()        # return the web-page content
            logging.info("Stored ical calendar %s in cache." % ical_key)
        self.response.headers['Content-Type'] = "text/calendar; charset=UTF-8; method=PUBLISH"
        self.response.out.write(content)
        return

