import webapp2
import model
import datetime
import lib
import urllib
from jinja_templates import jinja_environment
import datastore_index
import logging

logging.basicConfig(level=logging.INFO)


class DayHandler(webapp2.RequestHandler):
    def get(self, form='of', date_string='today', lang='en', iden=None):
        if date_string == 'today':
            date = datetime.date.today()
        else:
            date = datetime.datetime.strptime(date_string, '%Y-%m-%d').date()
        data = {}
        the_illustration = None
        the_other_illustrations = []
        # query for a matching date
        matching_date = model.Date.query_by_form_and_earliest_date(form, date)
        data['date'] = matching_date
        next_date = model.Date.query_by_form_and_earliest_date(form, date + datetime.timedelta(1))
        data['next'] = next_date
        previous_date = model.Date.query_by_form_and_later_date(form, date)
        data['previous'] = previous_date
        data['masses'] = [{
            'form': form,
            'coordinates': matching_date.mass,
            'cycle': matching_date.cycle
        }]
        if matching_date.coinciding:
            data['masses'].append({
                'form': form,
                'coordinates': matching_date.coinciding,
                'cycle': matching_date.cycle,
                'coinciding': True
            })
        for mass in data['masses']:
            # query for mass
            matching_mass = model.Mass.query_by_form_coordinates_and_cycle(
                mass['form'],
                mass['coordinates'],
                cycle=mass['cycle']
            )
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
                            reading['illustrations'] = []
                            # a bibleref contains itself !
                            for contained_bibleref in bibleref.containedReferences + [bibleref.reference]:
                                # query for verse
                                matching_verse = model.Verse.translate(contained_bibleref, lang)
                                # query for illustrations
                                matching_illustrations = model.Illustration.query_by_passageReference(contained_bibleref)
                                for matching_illustration in matching_illustrations:
                                    illustration = {}
                                    illustration['illustration'] = matching_illustration
                                    illustration['verse'] = matching_verse
                                    reading['illustrations'].append(illustration)
                                    if matching_illustration.filename == iden:
                                        the_illustration = illustration
                                    else:
                                        the_other_illustrations.append(illustration)
                            if reading['illustrations']:
                                mass['readings'].append(reading)
                            else:
                                logging.log(logging.ERROR, "No matching illustration at all for reading with bibleref=" + reading['bibleref'])
        the_mass = data['masses'][0]
        if the_mass['readings']:
            template = jinja_environment.get_template('day.html')
            the_reading = the_mass['readings'][0]
            if not the_illustration:
                the_illustration = the_reading['illustrations'][0]
                the_other_illustrations.remove(the_illustration)
            self.response.out.write(template.render(
                lang=lang,
                data=data,
                the_mass=the_mass,
                the_reading=the_reading,
                the_illustration=the_illustration,
                the_other_illustrations=the_other_illustrations,
                languages=datastore_index.LANGUAGES[the_mass['form']],
                translate=model.I18n.translate,
                quote=urllib.quote,
                url=url,
                slugify=lib.slugify,
                readable_date=lib.readable_date,
                canonical=None
            ))
            return
        else:
            logging.log(logging.CRITICAL,
                "No matching illustration at all for day with id = " +
                the_mass['form'] +
                '.' + the_mass['coordinates'] +
                ('.' + the_mass['cycle']) if the_mass['cycle'] else ''
            )
            self.response.out.write("Deze pagina is nog niet beschikbaar.")
            return


def url(date=None, lang=None, illustration=None, form=None):
    url = ''
    if form:
        url = url + '/' + form
    if date:
        url = url + '/' + date.date.strftime('%Y-%m-%d')
    if lang:
        url = url + '/' + lang
    if illustration:
        url = url + '/' + illustration['illustration'].filename
    return url