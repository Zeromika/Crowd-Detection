import argparse
import os
import sys
import time
from random import randint
import datetime
import numpy as np
import imutils
import math
import cv2
import sqlalchemy as db
import logging
import config
import json
from math import ceil

from crowd_detection import CrowdDetection, MaskObj

from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

def info_function(value):
    sys.stdout.write(json.dumps(dict(progress=ceil(value)), indent=2))
    sys.stdout.flush()

# Logging
logging.basicConfig(filename=str(config.LOG_PATH),level=config.LOGGING_LEVEL,format='%(asctime)s - %(message)s')
logging.info("Started Line Crossing Script")
logging.info("Logging Level : " + str(config.LOGGING_LEVEL))
logging.debug("Config Loaded")
logging.debug("DB_PATH = " + str(config.DB_DETAILS))

# Get id of the video to be processed.
try:
    args = sys.argv
    vid_id = args[1]
    logging.info("Parse Successfull")
except Exception as e:
    logging.error("Could not parse given data. Gracefully exiting...")
    sys.exit(500)


# DB Engine Create
# --------------------------------------------------
# TODO Swap to Environment Variables
# try:
#     DB_PATH = os.environ['DB_PATH']
# except:
#     DB_PATH = None
# If config DB_PATH is set use that engine instead
logging.warning("Initiating Database Engine")
DB_PATH = config.DB_DETAILS['DB_PATH']
if DB_PATH:
    engine = create_engine(DB_PATH, echo=False)
else:
    engine = create_engine('sqlite:///anomaly.db', echo=False)
Base = declarative_base()

# DB Connection Create
# ---------------------------------------------------------
Base.metadata.create_all(engine)
connection = engine.connect()
metadata = db.MetaData()


# Tables
# ---------------------------------------------------------
anomalies_table = db.Table('detected_anomalies', metadata, autoload=True, autoload_with=engine)
video_table = db.Table('videos',metadata,autoload=True, autoload_with=engine)
detected_objs_table = db.Table('detected_objects', metadata, autoload=True, autoload_with=engine)
video_anomalies_table = db.Table('video_detected_anomaly', metadata, autoload=True, autoload_with=engine)


# Important part in general we grab video details here
# ---------------------------------------------------------
video_details = connection.execute(db.select([video_table]).where(video_table._columns.video_id == vid_id)).fetchmany(1)[0]
vid_name = video_details['name']

width = video_details['width'] 
height = video_details['height']


test_engine = CrowdDetection(width=width, height=height)

detected_objs_details = connection.execute("SELECT * FROM detected_objects WHERE object_id = 1 AND video_id = " + str(vid_id)).fetchall()

def union(a,b):
    res = []
    x = min(a[0], b[0])
    y = min(a[1], b[1])
    w = max(a[0]+a[2], b[0]+b[2]) - x
    h = max(a[1]+a[3], b[1]+b[3]) - y
    res.append(x)
    res.append(y)
    res.append(w)
    res.append(h)
    return res

logging.info("Processing " + vid_name)
    
mask_objs = []
results = dict()
processed = 0
for item in detected_objs_details:
    logging.warning("Trying Masking Operation...")
    left_x = item['left_x']
    top_y = item['top_y']
    width = item['width']
    height = item['height']
    # Recieved Data is left_x, top_y
   
    ob_d = MaskObj(left_x,top_y,width,height)
    mask_objs.append(ob_d)
    results[item['detected_object_id']] = []
    for other_objs in detected_objs_details:
        if item != other_objs and item['frame_no'] == other_objs['frame_no']:
            left_x_other = other_objs['left_x']
            top_y_other = other_objs['top_y']
            width_other = other_objs['width']
            height_other = other_objs['height']
            ob_other = MaskObj(left_x_other, top_y_other, width_other, height_other)
            res = test_engine.getMaskingResult(ob_d, ob_other)
            if test_engine.getMaskingResult(ob_d, ob_other):
                results[item['detected_object_id']].append(other_objs['detected_object_id'])
    
    processed = processed + 1
    
    if len(results[item['detected_object_id']])>0 :
        union_box = []
        union_box.append(left_x)
        union_box.append(top_y)
        union_box.append(width)
        union_box.append(height)
        for i in results[item['detected_object_id']]:
            for r in detected_objs_details:
                if (i == r['detected_object_id']):
                    a = []
                    a.append(r['left_x'])
                    a.append(r['top_y'])
                    a.append(r['width'])
                    a.append(r['height'])
                    union_box = union(a=union_box, b=a)
        query = connection.execute(db.insert(anomalies_table).values(rule_id = 3,frame_no =item['frame_no'],left_x = union_box[0], top_y = union_box[1], width = union_box[2], height = union_box[3]), params = json.dumps(args) )
        connection.execute(db.insert(video_anomalies_table).values(detected_anomaly_id = query.lastrowid , video_id = vid_id))
    
    time.sleep(0.1) # Sleep half a second to process data
    info_function((processed/len(detected_objs_details)*100))
  
sys.exit(0)