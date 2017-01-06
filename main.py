import webapp2
from oauth2client.appengine import OAuth2Decorator
import google_credentials

decorator = OAuth2Decorator(client_id=google_credentials.CLIENT_ID,
                            client_secret=google_credentials.CLIENT_SECRET,
                            scope='https://spreadsheets.google.com/feeds https://www.googleapis.com/auth/drive')

routes = [
    webapp2.Route(r'/<form:of|eo>/<date_string:\d{4}-\d{2}-\d{2}>/<lang:en|nl|fr>/<iden:[-a-zA-Z0-9.]+>', handler='day.DayHandler'),
    webapp2.Route(r'/<form:of|eo>/<date_string:\d{4}-\d{2}-\d{2}>/<lang:en|nl|fr>', handler='day.DayHandler'),
    webapp2.Route(r'/<form:of|eo>/<date_string:\d{4}-\d{2}-\d{2}>', handler='day.DayHandler'),
    webapp2.Route(r'/<form:of|eo>/<lang:en|nl|fr>', handler='day.DayHandler'),
    webapp2.Route(r'/<date_string:\d{4}-\d{2}-\d{2}>/<lang:en|nl|fr>', handler='day.DayHandler'),
    webapp2.Route(r'/<form:of|eo>', handler='day.DayHandler'),
    webapp2.Route(r'/<date_string:\d{4}-\d{2}-\d{2}>', handler='day.DayHandler'),
    webapp2.Route(r'/<lang:en|nl|fr>', handler='day.DayHandler'),
    webapp2.Route(r'/', handler='day.DayHandler'),
    webapp2.Route(r'/pre/<form:of|eo>/<date_string:\d{4}-\d{2}-\d{2}>/<lang:en|nl|fr>', handler='day.DayHandlerPre'),
    webapp2.Route(r'/print/<lang:en|nl|fr>', handler='missal.PrintHandler'),
    webapp2.Route(r'/print/<lang:en|nl|fr>/<edition_only:.*>', handler='missal.PrintBookHandler'),
    webapp2.Route(r'/day/with', handler='day.LegacyHandler'),
    webapp2.Route(r'/inventory/<lang:en|nl|fr>', handler='inventory.InventoryHandler'),
    webapp2.Route(r'/rss/feed', handler='rss.RSSHandler'),
    webapp2.Route(r'/calendar/<form:of|eo>', handler='liturgy_calendar.XmlCalendarHandler'),
    webapp2.Route(r'/calendar-pickle/<form:of|eo>', handler='liturgy_calendar.PickleCalendarHandler'),
    webapp2.Route(r'/calendar/catholic-liturgy-<scope:sundays-and-feasts|weekdays>-<form:of|eo>-<lang:en|nl|fr>.ics', handler='liturgy_calendar.ICalendarHandler'),
    webapp2.Route(r'/missal/<lang:en|nl|fr>', handler='missal.MissalHandler'),
    webapp2.Route(r'/missal/<lang:en|nl|fr>/<references:.*>', handler='missal.QueryIllustrationsHandler'),
    webapp2.Route(r'/list-spreadsheet-illustrations', handler='spreadsheet_index.ListIllustrationsSpreadsheetHandler'),
    webapp2.Route(r'/sync-illustrations', handler='sync_illustration_index.SyncIllustrationHandler'),
    webapp2.Route(r'/sync-masses', handler='sync_masses_index.SyncMassesHandler'),
    webapp2.Route(r'/sync-i18n-terminology', handler='sync_i18n_index.SyncI18nTerminologyHandler'),
    webapp2.Route(r'/sync-i18n-of', handler='sync_i18n_index.SyncI18nOfHandler'),
    webapp2.Route(r'/sync-i18n-eo', handler='sync_i18n_index.SyncI18nEoHandler'),
    webapp2.Route(r'/sync-dates', handler='sync_dates.SyncDatesHandler'),
    webapp2.Route(r'/sync-verses', handler='sync_verses.SyncVersesHandler'),
    webapp2.Route(r'/sync-pagecount', handler='sync_pagecount_index.SyncPagecountHandler'),
    webapp2.Route(r'/flush-datastore-illustrations', handler='datastore_index.FlushIllustrationHandler'),
    webapp2.Route(r'/flush-datastore-masses', handler='datastore_index.FlushMassHandler'),
    webapp2.Route(r'/flush-i18n', handler='datastore_index.FlushI18nHandler'),
    webapp2.Route(r'/flush-datastore-verses', handler='datastore_index.FlushVerseHandler'),
    webapp2.Route(r'/flush-biblerefs', handler='bibleref.FlushBiblerefsHandler'),
    webapp2.Route(r'/flush-dates', handler='datastore_index.FlushDatesHandler'),
    webapp2.Route(r'/flush-pagecount', handler='datastore_index.FlushPagecountHandler'),
    webapp2.Route(decorator.callback_path, handler=decorator.callback_handler())
#    webapp2.Route(r'/oauth2callback', handler='oauth2_three_legged.OauthHandler')
]

app = webapp2.WSGIApplication(routes, debug=True)