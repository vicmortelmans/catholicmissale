import webapp2
import logging
import datastore_index
import lib
import model
import datetime
from jinja_templates import jinja_environment

logging.basicConfig(level=logging.INFO)


class CalendarHandler(webapp2.RequestHandler):
    def get(self, form='of'):
        # query the cache
        cache = model.Calendar_cache.get_or_insert(form)
        if cache.date == datetime.date.today():
            content = cache.content
        else:
            # get the datastore
            datastore_dates_mgr = datastore_index.Dates()
            dates = datastore_dates_mgr.sync_table()
            template = jinja_environment.get_template('liturgical_calendar.xml')
            content = template.render(
                form=form,
                dates=dates,  # list of dicts
                years=datastore_index.YEARS,
                languages=datastore_index.LANGUAGES,
                readable_date=lib.readable_date
            )
            # update cache
            cache.content = content
            cache.date = datetime.date.today()
            cache.put()
        self.response.headers['Content-Type'] = "application/xml"
        self.response.out.write(content)
        return
