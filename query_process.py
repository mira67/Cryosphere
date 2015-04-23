# [START imports]
import os
from google.appengine.ext import ndb
import cloudstorage as gcs
import numpy as np
import array
import math
import sys
from jpeg_bs_decoder import JpegDecoder
my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                          max_delay=5.0,
                                          backoff_factor=2,
                                          max_retry_period=15)
gcs.set_default_retry_params(my_default_retry_params)

#default data path
BUCKET = '/nsidc-0051'
MONTH_RP = '/monthly'
DAILY_RP = '/daily'
MONTH_CP = '/monthly_cmp'
DAILY_CP = '/daily_cmp'
TEST_CP = '/condense_jpg'
class QueryProc(object):

    def blk_total_seaice(self,blk):
        thr1 = 250
        thr2 = 37.5
        cell_size = 25#km
        seaice_area = len(blk[np.where(blk<=thr1)]) -  len(blk[np.where(blk<thr2)])
        seaice_area = math.floor(10*seaice_area*25.0*25.0/1000)#km^2,scaled by 10
        return seaice_area

    def maxmin_proc_raw(self):
        #get files list from gs
        objs = gcs.listbucket(BUCKET+MONTH_RP)
        filelist = []
        for obj in objs:
            filelist.append(obj.filename)
        #go through and calculate
        max_seaice = 0
        min_seaice = float('inf')
        result = []
        i = 0
        max_id = 0
        min_id = 0
        gcs_file = []
        raw_data = []
        for file in filelist:
            i = i + 1
            filename = file
            #raw_data = np.fromfile(filename, dtype=np.uint8, sep='')
            gcs_file = gcs.open(filename,mode='r')
            # Read the data into an array
            raw_file = gcs_file.read()
            raw_data = array.array('B',raw_file)
            raw_data = np.array(raw_data[300:])#offset 300 pixels
            raw_data = raw_data.reshape(316,332);
            total_seaice = self.blk_total_seaice(raw_data)
            if total_seaice >= max_seaice:
                max_id = i-1
                max_seaice = total_seaice
                min_seaice = max_seaice
            if total_seaice <= min_seaice:
                min_id = i-1
                min_seaice = total_seaice

            gcs_file.close()
            #for testing, DeadlineExceededError
            if i > 5:
                break

        result.append(max_seaice)
        result.append(max_id)
        result.append(min_seaice)
        result.append(min_id)
        #debugging
        return result 

    def maxmin_proc_cmp(self):
        #get files list from gs
        objs = gcs.listbucket(BUCKET+TEST_CP)
        filelist = []
        for obj in objs:
            filelist.append(obj.filename)
        
        #go through and calculate, need refine into modules later
        max_seaice = 0
        min_seaice = float('inf')
        result = []
        i = 0
        max_id = 0
        min_id = 0
        gcs_file = []
        raw_data = []
        dclist = []

        for file in filelist:
            i = i + 1
            filename = file
            gcs_file = gcs.open(filename,mode='r')
            
            jd = JpegDecoder()
            dclist = jd.jpdecode(gcs_file)
            gcs_file.close()

            #a new function
            ###parsed_dc = np.asarray(dclist)
            total_seaice = sum(dclist)
            if total_seaice >= max_seaice:
                max_id = i-1
                max_seaice = total_seaice
                min_seaice = max_seaice
            if total_seaice <= min_seaice:
                min_id = i-1
                min_seaice = total_seaice

            gcs_file.close()
            #for testing, DeadlineExceededError
            if i > 5:
                break

        result.append(max_seaice)
        result.append(max_id)
        result.append(min_seaice)
        result.append(min_id)

        return result #a list or dict




