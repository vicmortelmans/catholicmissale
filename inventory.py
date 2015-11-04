import webapp2
import model
import datetime
import lib
import urllib
from jinja_templates import jinja_environment
import datastore_index
import logging
import datastore_index

logging.basicConfig(level=logging.INFO)



class InventoryHandler(webapp2.RequestHandler):
    def get(self):
        datastore_masses_mgr = datastore_index.Masses()
        lookup_masses = datastore_masses_mgr.sync_lookup_table_by_reading()
        datastore_illustrations_mgr = datastore_index.Illustrations()
        datastore_illustrations = datastore_illustrations_mgr.sync_table()
        for illustration in datastore_illustrations:
            if illustration['passageReference']:
                bibleref = model.BibleRef.query_by_reference(illustration['passageReference'])
                illustration['book'] = bibleref.book
                illustration['chapter'] = (bibleref.begin / 1000) - 1000
                illustration['bibleref-begin'] = bibleref.begin
                containedReferences = bibleref.containedReferences
                containingReferences = [b.reference for b in model.BibleRef.query_by_containedReferences(bibleref.reference)]
                illustration['masses'] = []
                for contained_bibleref in containedReferences + [bibleref.reference] + containingReferences:
                    if contained_bibleref in lookup_masses:
                        illustration['masses'].extend(lookup_masses[contained_bibleref])
            else:
                logging.error("InventoryHandler found no passageReference in illustration with caption %s" % illustration['caption'])
                datastore_illustrations.remove(illustration)
        template = jinja_environment.get_template('inventory.html')
        content = template.render(
            illustrations=datastore_illustrations
        )
        # return the web-page content
        self.response.out.write(content)
        return


