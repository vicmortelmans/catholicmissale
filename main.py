import webapp2

routes = [
#    webapp2.Route(r'/<form:of|eo>/<date:\d{8}>/<lang:en|nl>/<iden:.{3}>', handler='day.DayHandler'),
#    webapp2.Route(r'/<form:of|eo>/<date:\d{8}>/<lang:en|nl>', handler='day.DayHandler'),
#    webapp2.Route(r'/<form:of|eo>/<date:\d{8}>', handler='day.DayHandler'),
#    webapp2.Route(r'/<form:of|eo>/<lang:en|nl>', handler='day.DayHandler'),
#    webapp2.Route(r'/<date:\d{8}>/<lang:en|nl>', handler='day.DayHandler'),
#    webapp2.Route(r'/<form:of|eo>', handler='day.DayHandler'),
#    webapp2.Route(r'/<date:\d{8}>', handler='day.DayHandler'),
#    webapp2.Route(r'/<lang:en|nl>', handler='day.DayHandler'),
#    webapp2.Route(r'/', handler='day.DayHandler'),
    webapp2.Route(r'/list-spreadsheet-illustrations', handler='spreadsheet_index.ListSpreadsheetHandler'),
    webapp2.Route(r'/sync-illustrations', handler='sync_illustration_index.SyncIllustrationHandler'),
    webapp2.Route(r'/sync-masses', handler='sync_masses_index.SyncMassesHandler'),
    webapp2.Route(r'/sync-i18n', handler='sync_i18n_index.SyncI18nHandler'),
    webapp2.Route(r'/sync-dates', handler='sync_dates.SyncDatesHandler'),
    webapp2.Route(r'/sync-verses', handler='sync_verses.SyncVersesHandler'),
    webapp2.Route(r'/flush-datastore-illustrations', handler='datastore_index.FlushIllustrationHandler'),
    webapp2.Route(r'/flush-datastore-masses', handler='datastore_index.FlushMassHandler'),
    webapp2.Route(r'/flush-i18n', handler='datastore_index.FlushI18nHandler'),
    webapp2.Route(r'/flush-datastore-verses', handler='datastore_index.FlushVerseHandler'),
    webapp2.Route(r'/flush-biblerefs', handler='bibleref.FlushBiblerefsHandler'),
    webapp2.Route(r'/oauth2callback', handler='oauth2_three_legged.OauthHandler')
]

app = webapp2.WSGIApplication(routes, debug=True)