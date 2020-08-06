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
import timeit
from tqdm import tqdm, trange
from colorama import Fore

# Cross-platform colored terminal text.
color_bars = [Fore.BLACK,
    Fore.RED,
    Fore.GREEN,
    Fore.YELLOW,
    Fore.BLUE,
    Fore.MAGENTA,
    Fore.CYAN,
    Fore.WHITE]

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
def add_to_map(ob):
    return ob

def json_to_mongodb():
    matches = []
    cities = list(map(add_to_map, coll_ci.aggregate([{"$group": { "_id": { "statename": "$statename", "cityname": "$cityname" } } }])))
    json_locations = None
    md = os.path.dirname(__file__)
    fpath = os.path.join(md, "towns-cities.json") 
    with open(fpath, "r+") as json_file:
        json_locations = list(map(add_to_map, json.load(json_file)))
    print("starting")
    for n in trange(len(cities), bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.RED, Fore.RESET), desc='mongo'):
        i = cities[n]['_id']
        for val in json_locations:
            c = False
            s = False
            match_ob = {'c': '', 's': '', 'a1': '', 'v1': '', 'a2': '', 'v2': '', 'lat': 0, 'lon': 0, 'node': ''}
            for attr, value in val['properties'].items():
                if c and s:
                    match_ob['lat'] = val['geometry']['coordinates'][1]
                    match_ob['lon'] = val['geometry']['coordinates'][0]
                    match_ob['node'] = val['id']
                    matches.append(match_ob)
                    break
                elif type(value) == type(i['cityname']):
                    c_search = re.search(re.compile(i['cityname'], re.IGNORECASE), value)
                    s_search = re.search(re.compile(i['statename'], re.IGNORECASE), value)
                    attr_search = re.search(re.compile(r"(county)|(is_in)", re.IGNORECASE), attr)
                    if c_search is not None and s_search is not None and attr_search is None:
                        c = True
                        s = True
                        match_ob['c'] = i['cityname']
                        match_ob['s'] = i['statename']
                        match_ob['a1'] = attr
                        match_ob['v1'] = value
                    elif c_search is not None and attr_search is None:
                        c = True
                        match_ob['c'] = i['cityname']
                        match_ob['a1'] = attr
                        match_ob['v1'] = value
                    elif s_search is not None:
                        s = True
                        match_ob['s'] = i['statename']
                        match_ob['a2'] = attr
                        match_ob['v2'] = value
    return matches

print(json_to_mongodb())



# code snippet to be executed only once 
mysetup = """
import os
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client.acedbv2
coll_ci = db.cities_city
def add_to_map(ob):
    return ob
cities = list(map(add_to_map, coll_ci.aggregate([{"$group": { "_id": { "statename": "$statename", "cityname": "$cityname" } } }])))
"""
  
# code snippet whose execution time is to be measured 
mycode = """ 
def example(): 
    return
"""
  
# timeit statement 
#print (timeit.timeit(setup = mysetup, stmt = mycode, number = 193324818))




def example():
    return


