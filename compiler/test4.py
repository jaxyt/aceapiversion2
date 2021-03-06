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
stopwords = stopwords.words('english')
import ngram
import timeit
from tqdm import tqdm, trange
from colorama import Fore
from fuzzywuzzy import process, fuzz
import urllib.parse
from django.template.defaultfilters import slugify

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
# coll_tel = db.registeredagents_telecomcorps
coll_tel = db.registeredagents_telecom

states = coll_ra.find().distinct('state')
cities = coll_ra.find().distinct('city')

def add_to_map(ob):
    return ob

def get_distinct_column_rows():
    #res = []
    #for i in coll_tel.find():
    #    res.append(json.dumps(i))
    # return pp.pformat(list(map(add_to_map, coll_tel.find())), indent=4)
    return json.dumps(list(map(add_to_map, coll_tel.find({}, {'_id': 0}))))

# print(get_distinct_column_rows())


def find_mistakes():
    query = re.compile('(none?;?)', re.IGNORECASE)
    for i in coll_tel.find({'dcagent1': query}):
        print(f"""
        {i['id']}
        {i['dcagent1']}
        """)
    query = re.compile('(systmes)', re.IGNORECASE)
    for i in coll_tel.find({'dcagent1': query}):
        print(f"""
        {i['id']}
        {i['dcagent1']}
        """)


results = []

for i in states:
    s = coll_st.find_one({'statename': f"{i}".lower()})
    for n in cities:
        try:
            c = coll_ci.find({'stateid': s['id'], 'cityname': f"{n}".lower()})
            for k in c:
                try:
                   results.append(f"{k['cityname']}".capitalize()+", "+f"{k['statename']}".capitalize())
                except Exception as e:
                    pass
        except Exception as e:
                pass

print(results)



