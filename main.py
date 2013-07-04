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
#    webapp2.Route(r'/list-datastore-illustrations', handler='datastore.ListDatastoreHandler'),
    webapp2.Route(r'/sync-illustrations', handler='sync_index.SyncHandler'),
    webapp2.Route(r'/oauth2callback', handler='oauth2_three_legged.OauthHandler'),
#    webapp2.Route(r'/load-illustrations', handler='illustrations.LoadHandler'),
#    webapp2.Route(r'/bulkload-illustrations', handler='bulkload.BulkloadIllustrations')
]

app = webapp2.WSGIApplication(routes, debug=True)