from model import BibleRef
import urllib
import urllib2
import json
import logging
import webapp2
import time


logging.basicConfig(level=logging.INFO)


def submit(reference, verses=False):
    """
    @param reference: a free text bible reference
    verses: TO DO
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
    for attempt in range(5):
        try:
            result = json.loads(urllib2.urlopen(url).read())['query']['results']  # TODO handle wrong results
            if not ('biblerefs' in result and 'bibleref' in result['biblerefs']):
                raise Exception('Empty results from YQL Bibleref open table for %s [%s]' % (reference, url))
        except Exception as error:  # catch any error
            logging.warning('On YQL Bibleref open table for %s, an http error occurred: %s [%s]' % (reference, error, url))
            time.sleep(0.5)
            continue
        else:
            break
    else:
        # we failed all the attempts - deal with the consequences.
        logging.info('On YQL Bibleref open table for %s, too many errors occurred [%s]' % (reference, url))
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
    others = BibleRef.query_by_book(book)
    for r in others:  # there's a problem here with split references...
        if e.begin <= r.begin and r.end <= e.end:
            e.containedReferences.append(r.reference)
        if r.begin <= e.begin and e.end <= r.end:
            r.containedReferences.append(reference)
            r.put()
    e.put()
    return reference


class FlushBiblerefsHandler(webapp2.RequestHandler):
    def get(self):
        BibleRef.flush()
        self.response.out.write("Flushed Bible references")