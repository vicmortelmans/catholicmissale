import webapp2
import model
import time
import datetime
import lib
import urllib
import logging
import day
import model
from jinja_templates import jinja_environment

logging.basicConfig(level=logging.INFO)


class RSSHandler(webapp2.RequestHandler):
    def get(self):
        form = self.request.get('form')
        lang = self.request.get('lang')
        if not self.request.get('date'):
            date = datetime.date.today()
        else:
            date = datetime.datetime.strptime(self.request.get('date'), '%Y-%m-%d').date()
        item_data = []
        # query the cache
        cache = model.RSS_cache.get_or_insert(lang + '.' + form)
        if cache.date == date:
            content = cache.content
        else:
            # query for a matching date
            matching_date = model.Date.query_by_form_and_earliest_date(form, date)
            if matching_date:
                item_data.append(day.get_all_data(matching_date, lang))
                for i in xrange(4):  # that is 0,1,2,3
                    # query for older dates
                    matching_date = model.Date.query_by_form_and_later_date(form, matching_date.date)
                    if matching_date:
                        data = day.get_all_data(matching_date, lang)
                        # set the pubDate of the previously appended data
                        item_data[-1]['pubDate'] = data['date'].date + datetime.timedelta(1)
                        if i < 3:
                            # don't append the last iteration, it won't have a publication date
                            item_data.append(data)
                    else:
                        break
            template = jinja_environment.get_template('rss.html')
            content = template.render(
                lang=lang,
                data=item_data,
                translate=model.I18n.translate,
                quote=urllib.quote,
                url=day.url,
                slugify=lib.slugify,
                readable_date=lib.readable_date,
                canonical=None,
                time=time
            )
            # update cache
            cache.content = content
            cache.date = date
            cache.put()
        self.response.headers['Content-Type'] = "application/rss+xml"
        self.response.out.write(content)

