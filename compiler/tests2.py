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

"""
sentences = [
    'This is a foo bar sentence.',
    'This sentence is similar to a foo bar sentence.',
    'This is another string, but it is not quite similar to the previous ones.',
    'I am also just another string.'
]

cleaned = list(map(clean_string, sentences))
vectorizer = CountVectorizer().fit_transform(cleaned)
vectors = vectorizer.toarray()
print(cosine_sim_vectors(vectors[0], vectors[1]))
"""

def lev_and_cos_search(searchterm):
    results = {}
    agents = list(map(add_to_map, coll_ra.find()))

    for n in trange(len(agents), bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.RED, Fore.RESET)):
        i = agents[n]
        sentences = [searchterm]
        combined = ""
        if i['company']:
            sentences.append(i['company'])
            combined += f"{i['company']} "
        if i['agency']:
            sentences.append(i['agency'])
            combined += f"{i['agency']} "
        if i['state']:
            sentences.append(i['state'])
            combined += f"{i['state']} "
        if i['city']:
            sentences.append(i['city'])
            combined += f"{i['city']}"
        sentences.append(combined)
        cleaned = list(map(clean_string, sentences))
        vectorizer = CountVectorizer().fit_transform(cleaned)
        vectors = vectorizer.toarray()
        #csim = cosine_similarity(vectors)
        similarities = []
        for k in vectors[1:]:
            similarities.append(cosine_sim_vectors(vectors[0], k))
        max_similarity = max(similarities)
        results[f"{i['id']}"] = max_similarity
    return results

for m in sorted(lev_and_cos_search('plantation fl').items(), key=lambda x: x[1], reverse=True)[0:10]:
    pp.pprint(coll_ra.find_one({'id': int(m[0])}))

