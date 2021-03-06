""""
# THIS FILE HAS BECOME OBSOLETE BY USING THE AOUTH DECORATOR
from oauth2client.client import OAuth2WebServerFlow
import google_credentials
from google.appengine.api import users
from oauth2client.appengine import CredentialsProperty
from oauth2client.appengine import StorageByKeyName
from gdata.gauth import OAuth2TokenFromCredentials
from apiclient.discovery import build
from google.appengine.ext import db
import webapp2
import httplib2
import urllib
import pickle


class CredentialsModel(db.Model):
    credentials = CredentialsProperty()


class Oauth2_service():

    def __init__(self, version, scope, api_client=None):
        request = webapp2.get_request()
        flow = OAuth2WebServerFlow(client_id=google_credentials.CLIENT_ID,
                                   client_secret=google_credentials.CLIENT_SECRET,
                                   scope=scope,
                                   redirect_uri=request.host_url + '/oauth2callback')
        user = users.get_current_user()
        cred = None
        if user:
            cred = CredentialsModel.get_by_key_name(user.user_id() + scope)
        else:
            login_url = users.create_login_url(request.url)
            webapp2.redirect(login_url, abort=True)
        if cred:
            credentials = cred.credentials
            if api_client:
                http = httplib2.Http()
                http = credentials.authorize(http)  # this takes care of refreshing the token if needed
                self.service = build(api_client, version, http=http)
            else:
                token = OAuth2TokenFromCredentials(credentials)  # this turns the google-api-python-client credentials
                # into a gdata token... wonder if it handles refresh...
                self.token = token
        else:
            state = {'original_url': request.url, 'scope': scope}
            state_string = pickle.dumps(state)
            auth_uri = flow.step1_get_authorize_url() + '&' + urllib.urlencode({'state': state_string})
            webapp2.redirect(auth_uri, abort=True)


class OauthHandler(webapp2.RequestHandler):

    def get(self):
        request = webapp2.get_request()
        code = request.get('code')
        state_string = request.get('state')
        state = pickle.loads(state_string)
        scope = state['scope']
        original_url = state['original_url']  # url of the original call
        flow = OAuth2WebServerFlow(client_id=google_credentials.CLIENT_ID,
                                   client_secret=google_credentials.CLIENT_SECRET,
                                   scope=scope,
                                   redirect_uri=request.path_url)
        credentials = flow.step2_exchange(code)
        user = users.get_current_user()
        storage = StorageByKeyName(CredentialsModel, user.user_id() + scope, 'credentials')
        storage.put(credentials)
        return webapp2.redirect(original_url)
"""
