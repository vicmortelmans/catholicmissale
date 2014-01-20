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
    id = ndb.TextProperty(required=True)  # form.coordinates(.cycle)
    form = ndb.StringProperty()
    coordinates = ndb.StringProperty()
    cycle = ndb.TextProperty()  # not repeated anymore
    name = ndb.TextProperty()
    category = ndb.TextProperty()
    color = ndb.TextProperty()
    season = ndb.TextProperty()
    order = ndb.IntegerProperty()
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
    id = ndb.TextProperty(required=True)  # lang.ref
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
    id = ndb.TextProperty(required=True)  # form.idx
    form = ndb.StringProperty()  # 'of' or 'eo'
    idx = ndb.IntegerProperty()  # sequential number
    mass = ndb.TextProperty()  # 'A011'
    coinciding = ndb.TextProperty()
    date = ndb.DateProperty()
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
            if d.cycle:
                key = ndb.Key(Mass, form + '.' + d.mass + '.' + d.cycle)
            else:
                key = ndb.Key(Mass, form + '.' + d.mass)
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
        return cls._query_by_form_and_date(
            form,
            date,
            lambda form, date: cls.query(cls.form == form, cls.date >= date).order(cls.date).fetch(14),
            lambda form, date: "No matching date >= " + date.strftime('%Y-%m-%d') + " for form = " + form
        )

    @classmethod
    def query_by_form_and_later_date(cls, form, date):
        return cls._query_by_form_and_date(
            form,
            date,
            lambda form, date: cls.query(cls.form == form, cls.date < date).order(-cls.date).fetch(14),
            lambda form, date: "No matching date < " + date.strftime('%Y-%m-%d') + " for form = " + form
        )

    @classmethod
    def query_by_form_and_idx(cls, form, idx):
        id = form + '.' + str(idx)
        r = cls.get_by_id(id)
        if not r:
            logging.log(logging.ERROR, "No matching date for form.idx = " + id)
        return r


class RSS_cache(ndb.Model):  # the key is lang.form
    date = ndb.DateProperty()
    content = ndb.TextProperty()
