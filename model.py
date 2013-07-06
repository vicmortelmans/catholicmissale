from google.appengine.ext import ndb


class Illustration(ndb.Model):
    id = ndb.StringProperty(required=True)
    title = ndb.StringProperty()
    artist = ndb.StringProperty()
    year = ndb.TextProperty()
    location = ndb.TextProperty()
    copyright = ndb.TextProperty()
    caption = ndb.TextProperty()
    filename = ndb.TextProperty()
    fileExtension = ndb.TextProperty()
    url = ndb.StringProperty

