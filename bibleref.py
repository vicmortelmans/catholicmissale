from model import BibleRef
from google.appengine.ext import ndb
import urllib
import urllib2
import json
import logging
import webapp2


logging.basicConfig(level=logging.INFO)


def submit(reference):
    """
    @param reference: a free text bible reference
    @return: None if the reference is already stored; the standard format of the reference
    if it is already stored in that format or if a new storage entity has been created
    """
    referenceFound = BibleRef.get_by_id(reference)
    if referenceFound:
        return None
    # the reference is not found in the datastore; try to find its standard format
    query = u"use 'http://github.com/vicmortelmans/yql-tables/raw/master/bible/bibleref.xml' as bible.bibleref;" + \
            u"select * from bible.bibleref where bibleref='{reference}' and language='en'"\
        .format(
            reference=reference
        )
    url = "http://query.yahooapis.com/v1/public/yql?q={query}&format=json"\
        .format(
            query=urllib.quote(query.encode('utf8'))
        )
    try:
        result = json.loads(urllib2.urlopen(url).read())['query']['results']  # TODO handle wrong results
        if not ('biblerefs' in result and 'bibleref' in result['biblerefs']):
            raise Exception('Empty results from YQL Bibleref open table')
    except Exception as error:  # catch any error
        logging.warning('On YQL, an http error occurred: %s' % error)
        return None  # better luck next time
    biblerefs = result['biblerefs']['bibleref']
    if type(biblerefs) is not list:  # happens if there's only one element
        biblerefs = [biblerefs]
    begin = biblerefs[0]
    end = biblerefs[-1]
    book = begin['osisbook']
    chapterversereference = begin['chapterversereference']
    reference = book + ' ' + chapterversereference
    referenceFound = BibleRef.get_by_id(reference)
    if referenceFound:
        return reference
    # the reference is still not found; create a new entity
    e = BibleRef.get_or_insert(reference, reference=reference)
    e.book = book
    e.begin = 1000000 + 1000 * int(begin['chapter']) + int(begin['verse'])
    e.end = 1000000 + 1000 * int(end['chapter']) + int(end['verse'])
    # and analyze it's relationship to the other references
    others = BibleRef.query_book(book)
    for r in others:
        if e.begin <= r.begin and r.end <= e.end:
            e.containedReferences.append(r.reference)
        if r.begin <= e.begin and e.end <= r.end:
            r.containedReferences.append(reference)
            r.put()
    e.put()
    return reference

def _flush():
    keys = BibleRef.query().fetch(keys_only=True)
    ndb.delete_multi(keys)

class FlushBiblerefsHandler(webapp2.RequestHandler):
    def get(self):
        _flush()
        self.response.out.write("Flushed Bible references")