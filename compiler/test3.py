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


def add_to_map(ob):
    return ob

def add_to_map_tuple(ob):
    return ob[1]

def clean_string(text):
    text = ''.join([word for word in text if word not in string.punctuation])
    text = text.lower()
    text = ' '.join([word for word in text.split() if word not in stopwords])

    return text

def cosine_sim_vectors(vec1, vec2):
    vec1 = vec1.reshape(1, -1)
    vec2 = vec2.reshape(1, -1)
    return cosine_similarity(vec1, vec2)[0][0]


def telecom_search(searchterm, model_keys):
    results = {}
    rats = {}
    agents = coll_te.find()
    for i in agents:
        str2Match = searchterm
        strOptions = [i[k] for k in model_keys if i[k]]
        highest = process.extractOne(str2Match,strOptions)[1]
        results[f"{i['id']}"] = highest
    #print(f"{sorted(results.items(), key=lambda x: x[1], reverse=True)[0]}")
    res = [coll_te.find_one({"id": int(l[0])}) for l in sorted(results.items(), key=lambda x: x[1], reverse=True) if l[1] > 50]
    return res
        

#  , ['carriername', 'businessname', 'holdingcompany', 'othertradename1', 'othertradename2', 'othertradename3', 'othertradename4', 'dcagent1', 'dcagent2', 'dcagentcity', 'dcagentstate', 'alternateagent1', 'alternateagent2', 'alternateagentcity', 'alternateagentstate']
#r = telecom_search(input("type a searchterm:  "), ['carriername', 'businessname', 'holdingcompany', 'othertradename1', 'othertradename2', 'othertradename3', 'othertradename4', 'dcagent1', 'dcagent2', 'dcagentcity', 'dcagentstate', 'alternateagent1', 'alternateagent2', 'alternateagentcity', 'alternateagentstate'])
#r = telecom_efficient_search(input("type a searchterm:  "), ['carriername', 'businessname', 'holdingcompany', 'othertradename1', 'othertradename2', 'othertradename3', 'othertradename4', 'dcagent1', 'dcagent2', 'dcagentcity', 'dcagentstate', 'alternateagent1', 'alternateagent2', 'alternateagentcity', 'alternateagentstate'])
#r = telecom_search(input("type a searchterm:  "), ['carriername', 'businessname', 'holdingcompany', 'othertradename1', 'othertradename2', 'othertradename3', 'othertradename4', 'dcagent1', 'dcagent2', 'dcagentcity', 'dcagentstate'])
#pp.pprint(f"high: {r[0]}")
#print(coll_te.find_one({"id":82}))


iter_result = list(map(lambda x: f"""<a href="/locations/{'-'.join(x['statename'].split(' '))}">{x['statename'].title()}</a>""", coll_st.find()))

print(iter_result)

