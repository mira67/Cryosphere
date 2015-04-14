"""Grab data from cloud storage and pre-process to store total sea ice/day
to Google datastore"""

from google.appengine.ext import ndb

#An entity model
class tot_seaice(ndb.Model):
  year = ndb.StringProperty()
  month = ndb.StringProperty()
  day = ndb.StringProperty()
  extent = ndb.IntegerProperty()

day_seaice = tot_seaice(year='2013',
                month='Jan',
                day='1',
                extent=5
                )
#store data
day_seaice_key = day_seaice.put()
