# [START imports]
import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb
import cloudstorage as gcs

import jinja2
import webapp2

import pprint
import logging

from google.appengine.api import app_identity

my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                          max_delay=5.0,
                                          backoff_factor=2,
                                          max_retry_period=15)
gcs.set_default_retry_params(my_default_retry_params)

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

DEFAULT_GUESTBOOK_NAME = 'default_guestbook'


# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):

        template_values ={}

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
        
        for i in range(1,11):
            day_seaice = Tot_seaice(year='2013',
            month='Jan',
            day='1',
            extent=5+i
            )
            #store data
            day_seaice_key = day_seaice.put()

        # [END main_page]

class Query(webapp2.RequestHandler):

    def post(self):
        user_query = self.request.get('query')
        #get query and test
        self.redirect('/?' + 'query_run')

# test here, then move to compute engine
class Tot_seaice(ndb.Model):
    year = ndb.StringProperty()
    month = ndb.StringProperty()
    day = ndb.StringProperty()
    extent = ndb.IntegerProperty()
          
application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/user_query', Query),
], debug=True)
