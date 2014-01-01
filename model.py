from google.appengine.ext import ndb


class Illustration(ndb.Model):
    """ the key is the same as the id field """
    id = ndb.StringProperty(required=True)
    title = ndb.StringProperty()
    artist = ndb.StringProperty()
    year = ndb.TextProperty()
    location = ndb.TextProperty()
    copyright = ndb.TextProperty()
    caption = ndb.TextProperty()
    filename = ndb.TextProperty()
    fileExtension = ndb.TextProperty()
    url = ndb.TextProperty()
    oldUrl = ndb.TextProperty()
    passageReference = ndb.TextProperty()
    wasted = ndb.TextProperty()

    @classmethod
    def flush(cls):
        keys = cls.query().fetch(keys_only=True)
        ndb.delete_multi(keys)


class Mass(ndb.Model):
    """ each day that has a mass sheet; no key is assigned [20131223 it is, isn't it?] """
    id = ndb.StringProperty(required=True)  # form.coordinates
    form = ndb.StringProperty()
    coordinates = ndb.StringProperty()
    cycle = ndb.StringProperty(repeated=True)
    name = ndb.TextProperty()
    category = ndb.TextProperty()
    color = ndb.TextProperty()
    season = ndb.TextProperty()
    order = ndb.IntegerProperty()
    gospel = ndb.StringProperty(repeated=True)
    lecture = ndb.StringProperty(repeated=True)
    epistle = ndb.StringProperty(repeated=True)

    @classmethod
    def flush(cls):
        keys = cls.query().fetch(keys_only=True)
        ndb.delete_multi(keys)


class BibleRef(ndb.Model):
    """ the key is the reference """
    reference = ndb.StringProperty(required=True)  # standardized bible reference
    book = ndb.StringProperty()  # please only 'osisbook' values as returned by bibleref yql open table
    begin = ndb.IntegerProperty()
    end = ndb.IntegerProperty()
    containedReferences = ndb.StringProperty(repeated=True)

    @classmethod
    def query_book(cls, book):
        return cls.query(cls.book == book)

    @classmethod
    def query_containing(cls, reference):
        return cls.query(cls.containedReferences == reference)

    @classmethod
    def flush(cls):
        keys = cls.query().fetch(keys_only=True)
        ndb.delete_multi(keys)

class I18n(ndb.Model):
    id = ndb.StringProperty(required=True)  # lang.ref
    ref = ndb.StringProperty()
    lang = ndb.StringProperty()
    string = ndb.StringProperty()

    @classmethod
    def translate(cls, ref, lang):
        return cls.get_by_id(lang + '.' + ref)


class Verse(ndb.Model):
    id = ndb.StringProperty(required=True)  # lang.ref
    ref = ndb.StringProperty()  # standardized bible reference
    lang = ndb.StringProperty()
    string = ndb.TextProperty()

    @classmethod
    def translate(cls, ref, lang):
        return cls.get_by_id(lang + '.' + ref)

    @classmethod
    def flush(cls):
        keys = cls.query().fetch(keys_only=True)
        ndb.delete_multi(keys)


class Date(ndb.Model):
    id = ndb.StringProperty(required=True)  # form.idx
    form = ndb.StringProperty()  # 'of' or 'eo'
    idx = ndb.IntegerProperty()  # sequential number
    mass = ndb.StringProperty()
    coinciding = ndb.StringProperty()
    date = ndb.DateProperty()

    @classmethod
    def flush(cls):
        keys = cls.query().fetch(keys_only=True)
        ndb.delete_multi(keys)
