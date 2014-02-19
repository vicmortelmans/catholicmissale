from google.appengine.ext import ndb
import logging

logging.basicConfig(level=logging.INFO)


ALL = 1000


class Illustration(ndb.Model):
    """ the key is the same as the id field """
    id = ndb.TextProperty(required=True)
    title = ndb.TextProperty()
    artist = ndb.TextProperty()
    year = ndb.TextProperty()
    location = ndb.TextProperty()
    copyright = ndb.TextProperty()
    caption = ndb.TextProperty()
    filename = ndb.TextProperty()
    fileExtension = ndb.TextProperty()
    url = ndb.TextProperty()
    oldUrl = ndb.TextProperty()
    passageReference = ndb.StringProperty()
    wasted = ndb.TextProperty()
    sync = ndb.TextProperty()

    @classmethod
    def flush(cls):
        keys = cls.query().fetch(keys_only=True)
        ndb.delete_multi(keys)

    @classmethod
    def query_by_passageReference(cls, passageReference):
        r = cls.query(cls.passageReference == passageReference).fetch(ALL)
        if not r:
            logging.log(logging.WARNING, "No matching illustration for passageReference = " + passageReference)
        return r


class Mass(ndb.Model):
    """ each day that has a mass sheet; no key is assigned [20131223 it is, isn't it?] """
    id = ndb.TextProperty(required=True)  # form.coordinates[+{1,2,3}][.cycle]
    form = ndb.TextProperty()
    coordinates = ndb.TextProperty()  # Z1225 and SOS carry iterator '+1' through '+3'
    cycle = ndb.TextProperty()  # not repeated anymore, so empty, 'A', 'B' or 'C'
    duplicate = ndb.BooleanProperty()  # true if cycle = 'B' or 'C' of repeated mass
    name = ndb.TextProperty()
    category = ndb.TextProperty()
    color = ndb.TextProperty()
    season = ndb.TextProperty()
    order = ndb.IntegerProperty(indexed=False)
    gospel = ndb.TextProperty(repeated=True)
    lecture = ndb.TextProperty(repeated=True)
    epistle = ndb.TextProperty(repeated=True)

    @classmethod
    def flush(cls):
        keys = cls.query().fetch(keys_only=True)
        ndb.delete_multi(keys)

    @classmethod
    def query_by_form_coordinates_and_cycle(cls, form, coordinates, cycle=None):
        id = form + '.' + coordinates
        if cycle:
            id = id + '.' + cycle
        r = cls.get_by_id(id)
        if not r:
            logging.log(logging.ERROR, "No matching mass for form.coordinates(.cycle) = " + id)
        return r

    # beware! Date is implementing it's own proprietory Mass queries !!


class BibleRef(ndb.Model):
    """ the key is the reference """
    reference = ndb.TextProperty(required=True)  # standardized bible reference
    book = ndb.StringProperty()  # please only 'osisbook' values as returned by bibleref yql open table
    begin = ndb.IntegerProperty()
    end = ndb.IntegerProperty()
    containedReferences = ndb.StringProperty(repeated=True)

    @classmethod
    def query_by_book(cls, book):
        return cls.query(cls.book == book).fetch(ALL)

    @classmethod
    def query_by_reference(cls, reference):
        r = cls.get_by_id(reference)
        if not r:
            logging.log(logging.ERROR, "No matching bibleref for reference = " + reference)
        return r

    @classmethod
    def query_by_containedReferences(cls, reference):
        return cls.query(cls.containedReferences == reference).fetch()

    @classmethod
    def flush(cls):
        keys = cls.query().fetch(keys_only=True)
        ndb.delete_multi(keys)

class I18n(ndb.Model):
    # check the spreadsheet for what value is used as ref
    id = ndb.TextProperty(required=True)  # lang.ref (lang.form.coordinates[+{1,2,3}] for liturgical days)
    ref = ndb.TextProperty()
    lang = ndb.TextProperty()
    string = ndb.TextProperty()

    @classmethod
    def translate(cls, ref, lang):
        id = lang + '.' + ref
        r = cls.get_by_id(id)
        if not r:
            logging.log(logging.ERROR, "No matching i18n for lang.ref = " + id)
        return r

    @classmethod
    def translate_liturgical_day(cls, form, coordinates, lang):
        # Z1225 and SOS carry iterator '+1' through '+3'
        id = lang + '.' + form + '.' + coordinates
        r = cls.get_by_id(id)
        if not r:
            logging.log(logging.ERROR, "No matching i18n for lang.form.coordinates = " + id)
        return r

    @classmethod
    def flush(cls):
        keys = cls.query().fetch(keys_only=True)
        ndb.delete_multi(keys)


class Verse(ndb.Model):
    id = ndb.TextProperty(required=True)  # lang.ref
    ref = ndb.TextProperty()  # standardized bible reference
    local_ref = ndb.TextProperty()  # bible reference with local book name
    lang = ndb.TextProperty()
    string = ndb.TextProperty()

    @classmethod
    def translate(cls, ref, lang):
        id = lang + '.' + ref
        r = cls.get_by_id(id)
        if not r:
            logging.log(logging.WARNING, "No matching verse for lang.ref = " + id)
        return r

    @classmethod
    def flush(cls):
        keys = cls.query().fetch(keys_only=True)
        ndb.delete_multi(keys)


class Date(ndb.Model):
    id = ndb.StringProperty(required=True)  # form.date
    form = ndb.TextProperty()  # 'of' or 'eo'
    mass = ndb.TextProperty()  # 'A011'
    coinciding = ndb.TextProperty()
    date = ndb.DateProperty(indexed=False)
    year = ndb.IntegerProperty(indexed=False)  # liturgical year !!
    cycle = ndb.TextProperty()

    @classmethod
    def flush(cls):
        keys = cls.query().fetch(keys_only=True)
        ndb.delete_multi(keys)

    @classmethod
    def _query_by_form_and_date(cls, form, date, q, l):
        # fetch 14 consecutive dates
        list_of_dates = q(form, date)
        # make 14 corresponding Mass keys
        list_of_mass_keys = []
        for d in list_of_dates:
            # I know, it's messy to solve data inconsistencies here
            # There's more in day.py ...
            if d.mass == 'Z1225' or d.mass == 'SOS':
                mass = str(d.mass) + '+1'
            else:
                mass = str(d.mass)
            if d.cycle:
                key = ndb.Key(Mass, form + '.' + mass + '.' + d.cycle)
            else:
                key = ndb.Key(Mass, form + '.' + mass)
            list_of_mass_keys.append(key)
        # try fetching Mass entities
        list_of_masses = ndb.get_multi(list_of_mass_keys)
        try:
            # find the first non-empty Mass entity
            index_of_first_match = next(i for i, j in enumerate(list_of_masses) if j)
        except StopIteration:
            logging.log(logging.ERROR, l(form, date))
            return
        return list_of_dates[index_of_first_match]

    @classmethod
    def query_by_form_and_earliest_date(cls, form, date):
        def q(form, date):
            id = form + '.' + date.strftime('%Y-%m-%d')
            if form == 'eo':
                return cls.query(cls.id >= id).filter(cls.id < 'of').order(cls.id).fetch(14)
            else:
                return cls.query(cls.id >= id).order(cls.id).fetch(14)
        def l(form, date):
            return "No matching date >= " + date.strftime('%Y-%m-%d') + " for form = " + form
        return cls._query_by_form_and_date(form, date, q, l)

    @classmethod
    def query_by_form_and_later_date(cls, form, date):
        def q(form, date):
            id = form + '.' + date.strftime('%Y-%m-%d')
            if form == 'of':
                return cls.query(cls.id < id).filter(cls.id > 'eo').order(-cls.id).fetch(14)
            else:
                return cls.query(cls.id < id).order(-cls.id).fetch(14)
        def l(form, date):
            return "No matching date < " + date.strftime('%Y-%m-%d') + " for form = " + form
        return cls._query_by_form_and_date(form, date, q, l)


class RSS_cache(ndb.Model):  # the key is lang.form
    date = ndb.DateProperty()
    content = ndb.TextProperty()


class Calendar_cache(ndb.Model):  # the key is form
    date = ndb.DateProperty()
    content = ndb.BlobProperty()


class Missal_cache(ndb.Model):  # the key is lang
    date = ndb.DateProperty()
    content = ndb.BlobProperty()
