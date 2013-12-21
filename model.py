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


class Mass(ndb.Model):
    """ each day that has a mass sheet; no key is assigned """
    key = ndb.StringProperty(required=True)
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


class BibleRef(ndb.Model):
    """ the key is the reference """
    reference = ndb.StringProperty(required=True)
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