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
    agents = list(map(add_to_map, coll_te.find()))

    for n in trange(len(agents), bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.RED, Fore.RESET)):
        i = agents[n]
        sentences = [searchterm]
        combined = ""
        for k in model_keys:
            if i[f'{k}']:
                sentences.append(i[f'{k}'])
                combined += f"{i[f'{k}']} "
        sentences.append(combined)
        cleaned = list(map(clean_string, sentences))
        vectorizer = CountVectorizer().fit_transform(cleaned)
        vectors = vectorizer.toarray()
        similarities = [cosine_sim_vectors(vectors[0], k) for k in vectors[1:]]
        avg_similarity = sum(similarities)/(len(similarities) + 1)
        results[f"{i['id']}"] = avg_similarity

    return sorted(results.items(), key=lambda x: x[1], reverse=True)


results = telecom_search("ver", ['carriername', 'businessname', 'holdingcompany', 'othertradename1', 'othertradename2', 'othertradename3', 'othertradename4', 'dcagent1', 'dcagent2', 'dcagentcity', 'dcagentstate', 'alternateagent1', 'alternateagent2', 'alternateagentcity', 'alternateagentstate'])
pp.pprint(results[0:100])
