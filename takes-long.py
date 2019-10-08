import webapp2
from oauth2client.appengine import OAuth2Decorator
import google_credentials

decorator = OAuth2Decorator(client_id=google_credentials.CLIENT_ID,
                            client_secret=google_credentials.CLIENT_SECRET,
                            scope='https://spreadsheets.google.com/feeds https://www.googleapis.com/auth/drive')

routes = [
    webapp2.Route(r'/inventory/<lang:en|nl|fr>', handler='inventory.InventoryHandler'),
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
