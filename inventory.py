import webapp2
import model
import datetime
from jinja_templates import jinja_environment
import logging
import datastore_index
import zlib
import urllib

logging.basicConfig(level=logging.INFO)



class InventoryHandler(webapp2.RequestHandler):
    def get(self, lang='en'):
        refresh = self.request.get('refresh')
        key = lang
        # query the cache
        cache = model.Inventory_cache.get_or_insert(key)
        if cache.content and not refresh:
            content = zlib.decompress(cache.content).decode('unicode_escape')
        else:
            datastore_masses_mgr = datastore_index.Masses()
            lookup_masses = datastore_masses_mgr.sync_lookup_table_by_reading()
            datastore_illustrations_mgr = datastore_index.Illustrations()
            datastore_illustrations = datastore_illustrations_mgr.sync_table()
            for illustration in datastore_illustrations:
                # an illustration has a bibleref
                # each bibleref links to other biblerefs, contained or containing and we have to find which of these
                # is the bibleref of a mass
                if illustration['passageReference']:
                    bibleref = model.BibleRef.query_by_reference(illustration['passageReference'])
                    if bibleref:
                        illustration['book'] = bibleref.book
                        illustration['chapter'] = (bibleref.begin / 1000) - 1000
                        illustration['bibleref-begin'] = bibleref.begin
                        containedReferences = bibleref.containedReferences
                        containingReferences = [b.reference for b in model.BibleRef.query_by_containedReferences(bibleref.reference)]
                        illustration['masses'] = []
                        track_masses = {}  # first collect masses in a dict by coordinates+form, to eliminate cycle duplicates
                        # for liturgical days with different readings each cycle, the cycle must match
                        # for liturgical days with same readings each cycle, the cycle is wildcard
                        for contained_bibleref in containedReferences + [bibleref.reference] + containingReferences:
                            if contained_bibleref in lookup_masses:
                                for mass in lookup_masses[contained_bibleref]:
                                    track = mass['coordinates'] + mass['form']
                                    if track not in track_masses or (mass['form'] == 'of' and track_masses[track]['cycle'] != mass['cycle']):
                                        mass['first_occurrence'] = model.Date.query_by_mass(mass['form'], mass['coordinates'], mass['cycle'])
                                        matching_i18n = model.I18n.translate_liturgical_day(mass['form'], mass['coordinates'], lang)
                                        mass['i18n'] = matching_i18n
                                        if track not in track_masses or (mass['duplicate'] and track_masses[track]['first_occurrence'] > mass['first_occurrence']):
                                            track_masses[track] = mass
                        illustration['masses'] = track_masses.values()
                        if not illustration['masses']:
                            logging.warning("No mass for %s" % bibleref)
                    else:
                        logging.warning("No bibleref for %s" % illustration['passageReference'])
                else:
                    logging.error("InventoryHandler found no passageReference in illustration with caption %s" % illustration['caption'])
                    datastore_illustrations.remove(illustration)
            template = jinja_environment.get_template('inventory.html')
            content = template.render(
                lang=lang,
                illustrations=datastore_illustrations,
                padded_book_index=padded_book_index,
                translate=model.I18n.translate,
                translate_bibleref=model.Verse.translate,
                quote=urllib.quote,
                languages=datastore_index.LANGUAGES['of']  # assuming 'eo' has same language list!
            )
            # update cache
            cache.content = zlib.compress(content.encode('unicode_escape'))
            cache.date = datetime.date.today()
            cache.put()
        # return the web-page content
        self.response.out.write(content)
        return


def padded_book_index(book):
    """
    :param book: name of the book, e.g. '1John'
    :return: number of the book in the sequence of the bible
    """
    index = {
        "Gen": "1",
        "Exod": "2",
        "Lev": "3",
        "Num": "4",
        "Deut": "5",
        "Josh": "6",
        "Judg": "7",
        "Ruth": "8",
        "1Sam": "9",
        "2Sam": "10",
        "1Kgs": "11",
        "1Chr": "13",
        "2Chr": "14",
        "Ezra": "15",
        "Neh": "16",
        "Tob": "17",
        "Jdt": "18",
        "Esth AddEsth": "19",
        "1Macc": "20",
        "2Macc": "21",
        "Job": "22",
        "Ps": "23",
        "Prov": "24",
        "Eccl": "25",
        "Song": "26",
        "Wis": "27",
        "Sir": "28",
        "Isa": "29",
        "Jer": "30",
        "Lam": "31",
        "Bar": "32",
        "Ezek": "33",
        "Dan": "34",
        "Hos": "35",
        "Joel": "36",
        "Amos": "37",
        "Obad": "38",
        "Jonah": "39",
        "Mic": "40",
        "Nah": "41",
        "Hab": "42",
        "Zeph": "43",
        "Hag": "44",
        "Zech": "45",
        "Mal": "46",
        "Matt": "47",
        "Mark": "48",
        "Luke": "49",
        "John": "50",
        "Acts": "51",
        "Rom": "52",
        "1Cor": "53",
        "2Cor": "54",
        "Gal": "55",
        "Eph": "56",
        "Phil": "57",
        "Col": "58",
        "1Thess": "59",
        "2Thess": "60",
        "1Tim": "61",
        "2Tim": "62",
        "Titus": "63",
        "Phlm": "64",
        "Heb": "65",
        "Jas": "66",
        "1Pet": "67",
        "2Pet": "68",
        "1John": "69",
        "2John": "70",
        "3John": "71",
        "Jude": "72",
        "Rev": "73"
    }
    return "%02d" % int(index[book] if book in index else "99")