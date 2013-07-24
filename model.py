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
    passageReferences = ndb.TextProperty()


class Mass(ndb.Model):
    """ each day that has a mass sheet; no key is assigned """
    key = ndb.StringProperty(required=True)
    name = ndb.TextProperty()
    coordinates = ndb.StringProperty()
    form = ndb.StringProperty()
    cycle = ndb.StringProperty(repeated=True)
    season = ndb.TextProperty()
    color = ndb.TextProperty()
    order = ndb.IntegerProperty()
    gospel = ndb.StringProperty(repeated=True)
    lecture = ndb.StringProperty(repeated=True)
    epistle = ndb.StringProperty(repeated=True)
    coincidesWith = ndb.TextProperty()


class BibleRef(ndb.Model):
    """ the key is the reference """
    reference = ndb.StringProperty(required=True)
    book = ndb.StringProperty()
    begin = ndb.IntegerProperty()
    end = ndb.IntegerProperty()
    containedReferences = ndb.StringProperty(repeated=True)

    @classmethod
    def query_book(cls, book):
        return cls.query(cls.book == book)