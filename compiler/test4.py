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
coll_tel = db.registeredagents_telecomcorps

def add_to_map(ob):
    return ob

def get_distinct_column_rows():
    #res = []
    #for i in coll_tel.find():
    #    res.append(json.dumps(i))
    # return pp.pformat(list(map(add_to_map, coll_tel.find())), indent=4)
    return json.dumps(list(map(add_to_map, coll_tel.find())), indent=4)

print(get_distinct_column_rows())



