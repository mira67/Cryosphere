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
import time

from google.appengine.api import app_identity
from query_process import QueryProc

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

# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):

        template_values ={}

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
        
        #for i in range(1,11):
         #   day_seaice = Tot_seaice(year='2013',
          #  month='Jan',
           # day='1',
            #extent=5+i
            #)
            #store data
            #day_seaice_key = day_seaice.put()

        # [END main_page]

class Query(webapp2.RequestHandler):

    def post(self):
        user_query = self.request.get('query')
        user_query_c = user_query.upper()
        #QUERY for MAX MIN EXTENT, result should be the day, and show image
        if user_query_c == 'MAX MIN EXTENT':
            #call processing module
            query_process = QueryProc()

            start_time = time.time()
            query_raw_results = query_process.maxmin_proc_raw()
            query_raw_time = time.time() - start_time                        
            
            start_time = time.time()
            query_cmp_results = query_process.maxmin_proc_cmp()
            query_cmp_time = time.time() - start_time

            #store image and just show, no interactive as first version

            
            #call the function, need wrap this update into a function
            template_values = {
            'user_input': "User's Query: " + user_query_c,
            'query_result': "Raw: " + str(query_raw_results) + " " + "vs " +"CMP: " + str(query_cmp_results),
            'proc_time': "Process raw time: %s vs Process cmp time: %s" % (query_raw_time, query_cmp_time)
            }

            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values)) 

        #QUERY for Anomaly analysis, show the trend and std
        elif user_query_c == 'SEA ICE EXTENT ANOMALY':
            self.response.write("here is the query %s" % user_query_c) 
        else:
            self.response.write('This query might be supported in future version') 
        #QUERY is currently no supported
        #self.redirect('/?' + 'query_run')

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
