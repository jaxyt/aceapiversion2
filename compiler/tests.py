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
import Levenshtein
import string
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords
stw = stopwords.words('english')
import ngram

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
coll_te = db.registeredagents_telecomcorps

arra = ["", "registered-agents", "search", "state", "mi"]

def clean_text(text):
    text = ''.join([word for word in text if word not in string.punctuation])
    text = text.lower()
    text = ' '.join([word for word in text.split() if word not in stw])
    return text

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


#  locs = location_search_func(arra)

# arra2 = ["", "registered-agents", "search", "state", "ct del"]
arra2 = ["", "registered-agents", "search", "state", "csc del"]
def text_score_search(arr):
    res = []
    k = arr[3]
    # q = re.sub(r"[^A-z0-9\s]+", "", arr[4])
    q = clean_text(arr[4])
    qu = "("+re.sub(r"\s+", ")|(", q.strip())+")"
    query = re.compile(qu, re.IGNORECASE)
    for i in coll_ra.aggregate([{"$match": {"$or" : [{"company": query},{"agency": query},{"state": query},{"city": query}]}},{"$sort": { k: 1 }}]):
        res.append(i)
    return sort_results(res, q)

def sort_results(results, quer):
    scores = []
    sorted_scores = []
    for i in results:
        scores.append({"obj": i, "avg": ((Levenshtein.distance(quer, clean_text(i['company'])))+(Levenshtein.distance(quer, clean_text(i['agency'])))+(Levenshtein.distance(quer, clean_text(i['state'])))+(Levenshtein.distance(quer, clean_text(i['city']))))/4})
    for i in scores:
        if len(sorted_scores) == 0:
            sorted_scores.append(i)
        else:
            for idx, val in enumerate(sorted_scores):
                if i['avg'] <= val['avg']:
                    sorted_scores.insert(idx, i)
                    break
    return sorted_scores

#for k in text_score_search(arra2):
    #print(f"{k['avg']}: {k['obj']['company']} | {k['obj']['agency']} | {k['obj']['city']} | {k['obj']['state']}")

#for m in text_score_search(arra2):
    # print(f"{m['averagescore']} - {max(m['scorearr'])} : {m['obj']['company']} | {m['obj']['agency']} | {m['obj']['city']} | {m['obj']['state']}")
    #print(m)


#  print(locs[0:5])

def minify_js(sid, rt):
    site = coll_si.find_one({"id": sid})
    for i in site['pages']:
        if i['route'] == rt:
            return re.sub(r'\s{2,}', " ", i['content'])

#script = minify_js(4, "/script.js")
#print(script)

#  cleaned = list(map(clean_string, sentences))

def json_to_mongodb():
    md = os.path.dirname(__file__)
    fpath = os.path.join(md, "towns-cities.json")
    with open(fpath, "r+") as json_file:
        matches = ["done"]
        data = json.load(json_file)
        for cnt, i in enumerate(coll_ci.find()):
            if cnt > 1000:
                break
            else:
                for idx, val in enumerate(data):
                    match_ob = f"""{i["cityname"]} |"""
                    for attr, value in val['properties'].items():
                        if type(value) == type(i['cityname']):
                            reg = re.compile(i['cityname'], re.IGNORECASE)
                            if re.search(reg, value) is not None:
                                for a, v in val['properties'].items():
                                    if type(v) == type(i['statename']):
                                        reg = re.compile(i['statename'], re.IGNORECASE)
                                        if re.search(reg, v) is not None:
                                            match_ob += f""" / {attr}: {value}; {a}: {v}; {val['geometry']['coordinates'][1]}, {val['geometry']['coordinates'][0]}; {val['id']} /"""
                                            print(match_ob)
                                            break
                                break
        return matches

m = json_to_mongodb()
for i in m:
    print(i)

