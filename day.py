import webapp2
import model
import datetime
import lib
import urllib
from jinja_templates import jinja_environment
import datastore_index
import logging
import json
import re

logging.basicConfig(level=logging.INFO)

subscription_form = {
    'of': {
        'en': "https://eepurl.com/M8wpL",
        'nl': "https://eepurl.com/M8wo9",
        'fr': "https://eepurl.com/M8sGL"
    },
    'eo': {
        'en': "https://eepurl.com/M8wn1",
        'nl': "https://eepurl.com/M8wov",
        'fr': "https://eepurl.com/M8s9D"
    }
}


class LegacyHandler(webapp2.RequestHandler):
    def get(self):
        form = self.request.get('form')
        lang = self.request.get('lang')
        date_string = self.request.get('date')
        self.redirect(url(form=form, lang=lang, date=date_string), True)
        return


class DayHandler(webapp2.RequestHandler):
    def get(self, form='of', date_string='today', lang='en', iden=None, pre=False):
        if date_string == 'today':
            date = datetime.date.today()
        else:
            date = datetime.datetime.strptime(date_string, '%Y-%m-%d').date()
        # query for a matching date
        if pre:
            matching_date = model.Date.query_by_form_and_latest_date(form, date)
        else:
            matching_date = model.Date.query_by_form_and_earliest_date(form, date)
        if not matching_date:
            logging.log(logging.CRITICAL, "No matching date %s %s for %s form." % (
                "before" if pre else "after",
                date,
                "ordinary" if form == "of" else "extraordinary"
            ))
            self.response.out.write("Deze pagina is nog niet beschikbaar.")
            return
        data = get_all_data(matching_date, lang, iden)
        if not data:
            logging.log(logging.CRITICAL,
                "No matching illustration at all for day with id = " +
                data['the_mass']['form'] +
                '.' + data['the_mass']['coordinates'] +
                ('.' + data['the_mass']['cycle']) if data['the_mass']['cycle'] else ''
            )
            self.response.out.write("Deze pagina is nog niet beschikbaar.")
            return
        # query for previous and next dates
        next_date = model.Date.query_by_form_and_earliest_date(form, matching_date.date + datetime.timedelta(1))
        previous_date = model.Date.query_by_form_and_later_date(form, matching_date.date)
        template = jinja_environment.get_template('day2.html')
        # compose lectionary url
        lectionary_url_readings = (
            ("title", data["the_mass"]['i18n'].string.encode('utf-8')),
            ("subtitle", lib.readable_date(data['date'].date, lang).encode('utf-8')),
            ("language", lang)
        )
        if form == "of":
            for bibleref in data['the_mass']['mass'].lecture:
                lectionary_url_readings += ((model.I18n.translate("lecture", lang).string.capitalize().encode('utf-8'), bibleref),)
            for bibleref in data['the_mass']['mass'].epistle:
                lectionary_url_readings += ((model.I18n.translate("second-reading", lang).string.capitalize().encode('utf-8'), bibleref),)
        else:
            for bibleref in data['the_mass']['mass'].epistle:
                lectionary_url_readings += ((model.I18n.translate("epistel", lang).string.capitalize().encode('utf-8'), bibleref),)
        for bibleref in data['the_mass']['mass'].gospel:
            lectionary_url_readings += ((model.I18n.translate("gospel", lang).string.capitalize().encode('utf-8'), bibleref),)
        lectionary_url = "https://alledaags.gelovenleren.net/lectionarium?" + urllib.urlencode(lectionary_url_readings)
        # compose the web-page content
        content = template.render(
            lang=lang,
            data=data,
            next=next_date,
            prev=previous_date,
            the_mass=data['the_mass'],
            the_reading=data['the_reading'],
            the_illustration=data['the_illustration'],
            the_other_illustrations=data['the_other_illustrations'],
            languages=datastore_index.LANGUAGES[data['the_mass']['form']],
            translate=model.I18n.translate,
            quote=urllib.quote,
            url=url,
            slugify=lib.slugify,
            readable_date=lib.readable_date,
            subscription_form=subscription_form[form][lang],
            lectionary_url=lectionary_url,
            re=re
        )
        # return the web-page content
        self.response.out.write(content)
        return


class DayHandlerPre(DayHandler):
    def get(self, form='of', date_string='today', lang='en', iden=None, pre=True):
        DayHandler.get(self, form=form, date_string=date_string, lang=lang, iden=iden, pre=pre)
        return


class JsonHandler(webapp2.RequestHandler):
    def get(self, form='of', date_string='today', lang='en', reading_type='gospel'):
        if date_string == 'today':
            date = datetime.date.today()
        else:
            date = datetime.datetime.strptime(date_string, '%Y-%m-%d').date()
        # query for a matching date
        matching_date = model.Date.query_by_form_and_earliest_date(form, date)
        if not matching_date:
            logging.log(logging.CRITICAL, "No matching date %s %s for %s form." % (
                "after",
                date,
                "ordinary" if form == "of" else "extraordinary"
            ))
            self.response.out.write("Deze pagina is nog niet beschikbaar.")
            return
        mass = get_mass(matching_date, lang)
        if not mass:
            logging.log(logging.CRITICAL, "No matching mass at all")
            self.response.out.write("Deze pagina is nog niet beschikbaar.")
            return
        biblerefs = getattr(mass['mass'], reading_type) if hasattr(mass['mass'], reading_type) else []
        response = json.dumps({
            "date": matching_date.date.strftime('%Y-%m-%d'),
            "spokendate": lib.readable_date(matching_date.date, lang),
            "day": mass['i18n'].string,
            "readingtype": reading_type,
            "bibleref": biblerefs[0] if biblerefs else ''
        })
        logging.info(response)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(response)
        return


def get_all_data(date, lang, iden=''):
    form = date.form
    data = {}
    data['form'] = form
    data['date'] = date  # date is my own Date object!!
    data['masses'] = [{
        'form': form,
        'coordinates': date.mass,
        'cycle': date.cycle
    }]
    if date.coinciding:
        data['masses'].append({
            'form': form,
            'coordinates': date.coinciding,
            'cycle': date.cycle,
            'coinciding': True
        })
    data['the_illustration'] = None
    data['the_other_illustrations'] = []
    for mass in data['masses']:
        # query for mass
        # I know, it's messy to solve data inconsistencies here
        # There's more in model.py ...
        if mass['coordinates'] == 'Z1225' or mass['coordinates'] == 'SOS':
            matching_masses = [
                model.Mass.query_by_form_coordinates_and_cycle(
                    mass['form'],
                    mass['coordinates'] + iterator,
                    cycle=mass['cycle']
                )
                for iterator in ['+1', '+2', '+3']
            ]
        else:
            matching_masses = [
                model.Mass.query_by_form_coordinates_and_cycle(
                    mass['form'],
                    mass['coordinates'],
                    cycle=mass['cycle']
                )
            ]
        for matching_mass in matching_masses:
            mass['mass'] = matching_mass
            # query for i18n mass name
            matching_i18n = model.I18n.translate_liturgical_day(mass['form'], mass['coordinates'], lang)
            mass['i18n'] = matching_i18n
            mass['readings'] = []
            for reading_type in ['gospel', 'lecture', 'epistle']:
                if hasattr(mass['mass'], reading_type):
                    for bibleref in getattr(mass['mass'], reading_type):
                        reading = {}
                        reading['type'] = reading_type
                        reading['bibleref'] = bibleref
                        if reading['bibleref']:
                            # query for bibleref
                            bibleref = model.BibleRef.query_by_reference(reading['bibleref'])
                            containedReferences = bibleref.containedReferences
                            if containedReferences:
                                logging.log(logging.INFO, "Contained references for %s: %s" % (reading['bibleref'], ','.join(containedReferences)))
                            containingReferences = [b.reference for b in model.BibleRef.query_by_containedReferences(reading['bibleref'])]
                            if containingReferences:
                                logging.log(logging.INFO, "References containing %s: %s" % (reading['bibleref'], ','.join(containingReferences)))
                            reading['illustrations'] = []
                            # a bibleref contains itself !
                            for contained_bibleref in containedReferences + [bibleref.reference] + containingReferences:
                                # query for illustrations by searching for the bibleref itself and all contained and containing biblerefs
                                matching_illustrations = model.Illustration.query_by_passageReference(contained_bibleref)
                                for matching_illustration in matching_illustrations:
                                    illustration = {}
                                    illustration['illustration'] = matching_illustration
                                    reading['illustrations'].append(illustration)
                                    if matching_illustration.filename == iden:
                                        data['the_illustration'] = illustration
                                    else:
                                        data['the_other_illustrations'].append(illustration)
                            if reading['illustrations']:
                                mass['readings'].append(reading)
                            else:
                                logging.log(logging.ERROR, "No matching illustration at all for reading with bibleref=" + reading['bibleref'])
    data['the_mass'] = data['masses'][0]
    if data['the_mass']['readings']:
        data['the_reading'] = data['the_mass']['readings'][0]
        if not data['the_illustration']:
            data['the_illustration'] = data['the_reading']['illustrations'][0]
            data['the_other_illustrations'].remove(data['the_illustration'])
        # query for verse
        matching_verse = model.Verse.translate(data['the_illustration']['illustration'].passageReference, lang)
        data['the_illustration']['verse'] = matching_verse
        if not matching_verse:
            logging.log(logging.ERROR, "No matching verse for %s in %s" % (data['the_illustration']['illustration'].passageReference, lang))
        return data
    else:
        return None


def get_mass(date, lang):
    form = date.form
    data = {}
    data['form'] = form
    data['date'] = date  # date is my own Date object!!
    data['masses'] = [{
                          'form': form,
                          'coordinates': date.mass,
                          'cycle': date.cycle
                      }]
    if date.coinciding:
        data['masses'].append({
            'form': form,
            'coordinates': date.coinciding,
            'cycle': date.cycle,
            'coinciding': True
        })
    for mass in data['masses']:
        # query for mass
        # I know, it's messy to solve data inconsistencies here
        # There's more in model.py ...
        if mass['coordinates'] == 'Z1225' or mass['coordinates'] == 'SOS':
            matching_masses = [
                model.Mass.query_by_form_coordinates_and_cycle(
                    mass['form'],
                    mass['coordinates'] + iterator,
                    cycle=mass['cycle']
                )
                for iterator in ['+1', '+2', '+3']
            ]
        else:
            matching_masses = [
                model.Mass.query_by_form_coordinates_and_cycle(
                    mass['form'],
                    mass['coordinates'],
                    cycle=mass['cycle']
                )
            ]
    matching_mass = matching_masses[0]
    mass['mass'] = matching_mass
    matching_i18n = model.I18n.translate_liturgical_day(mass['form'], mass['coordinates'], lang)
    mass['i18n'] = matching_i18n
    return mass


def url(date=None, lang=None, illustration=None, form=None):
    """
    @param date: a Date object (see model.py) or a date string in format YYYY-MM-DD
    @param lang: 'en' or 'nl' or...
    @param illustration: a string
    @param form: 'of' or 'eo'
    @return: the URL path (starting with '/', without domain!)
    """
    if date and not isinstance(date, basestring):
        date = date.date.strftime('%Y-%m-%d')
    url = ''
    if form:
        url = url + '/' + form
    if date:
        url = url + '/' + date
    if lang:
        url = url + '/' + lang
    if illustration:
        url = url + '/' + illustration['illustration'].filename
    return url