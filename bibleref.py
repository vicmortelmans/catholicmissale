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
    url = "https://catecheserooster.appspot.com/yql/bibleref?bibleref={reference}&language=en&tolerance=true"\
        .format(
            reference=urllib.quote(reference.encode('utf8'))
        )
    for attempt in range(5):
        try:
            logging.info("Submitting bibleref " + reference + " ;REST call to " + url)
            result = json.loads(urllib2.urlopen(url).read())  # TODO handle wrong results
            if not (result):
                raise Exception('Empty results from Bibleref API for %s [%s]' % (reference, url))
        except Exception as error:  # catch any error
            logging.warning('On Bibleref API for %s, an http error occurred: %s [%s]' % (reference, error, url))
            time.sleep(0.5)
            continue
        else:
            break
    else:
        # we failed all the attempts - deal with the consequences.
        logging.error('On Bibleref API for %s, too many errors occurred [%s]' % (reference, url))
        return None  # better luck next time
    biblerefs = result
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