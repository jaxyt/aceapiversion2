# from django.test import TestCase
# Create your tests here.
import pymongo
import re
import json
import datetime
import os
import pprint as pp
from pymongo import MongoClient
from similar_text import similar_text

client = MongoClient('mongodb://localhost:27017/')
db = client.acedbv2

coll_ra = db.registeredagents_registeredagent
coll_st = db.states_state
coll_co = db.counties_county
coll_ci = db.cities_city
coll_si = db.sites_site
coll_te = db.templates_template
coll_bl = db.blogs_blog
coll_cp = db.registeredagents_corporation

arra = ["", "registered-agents", "search", "state", "mi"]

def location_search_func(arr):
    locations = []
    k = arr[3]
    query = re.compile(arr[4], re.IGNORECASE)
    for i in coll_ci.aggregate([{"$match": {"$or" : [{"statename": query},{"countyname": query},{"cityname": query}]}},{"$project": {"cityngram": 0}},{"$sort": { f"{k}name": 1 }}]):
        state_sim = similar_text(arr[4], i['statename'])
        county_sim = similar_text(arr[4], i['countyname'])
        city_sim = similar_text(arr[4], i['cityname'])
        similarity = {"type": "city", "score": city_sim} if city_sim >= county_sim and city_sim >= state_sim else {"type": "county", "score": county_sim} if county_sim >= city_sim and county_sim >= state_sim else {"type": "state", "score": state_sim} if state_sim >= county_sim and state_sim >= city_sim else {"type": "city", "score": city_sim}
        link = "/locations"
        if similarity['type'] == "city":
            link += f"/{i['statename']}/{i['countyname']}/{i['cityname']}"
        if similarity['type'] == "county":
            link += f"/{i['statename']}/{i['countyname']}"
        if similarity['type'] == "state":
            link += f"/{i['statename']}"
        location = {"loc": i, "sim": similarity, "link": link}
        if len(locations) == 0 or location['sim']['score'] <= locations[len(locations) - 1]['sim']['score']:
            locations.append(location)
        else:
            for idx, val in enumerate(locations):
                if location['sim']['score'] >= val['sim']['score']:
                    locations.insert(idx, location)
                    break
    return locations


locs = location_search_func(arra)

#  print(locs[0:5])

def minify_js(sid, rt):
    site = coll_si.find_one({"id": sid})
    for i in site['pages']:
        if i['route'] == rt:
            return re.sub(r'\s{2,}', " ", i['content'])

#script = minify_js(4, "/script.js")
#print(script)

def check_for_change():
    return "please work"

print(check_for_change())
