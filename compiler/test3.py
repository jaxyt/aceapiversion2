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
coll_tel = db.registeredagents_telecomcorps


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
    agents = coll_tel.find()
    for i in agents:
        str2Match = searchterm
        strOptions = [i[k] for k in model_keys if i[k]]
        highest = process.extractOne(str2Match,strOptions)[1]
        results[f"{i['id']}"] = highest
    #print(f"{sorted(results.items(), key=lambda x: x[1], reverse=True)[0]}")
    res = [coll_tel.find_one({"id": int(l[0])}) for l in sorted(results.items(), key=lambda x: x[1], reverse=True) if l[1] > 50]
    return res
        

#  , ['carriername', 'businessname', 'holdingcompany', 'othertradename1', 'othertradename2', 'othertradename3', 'othertradename4', 'dcagent1', 'dcagent2', 'dcagentcity', 'dcagentstate', 'alternateagent1', 'alternateagent2', 'alternateagentcity', 'alternateagentstate']
#r = telecom_search(input("type a searchterm:  "), ['carriername', 'businessname', 'holdingcompany', 'othertradename1', 'othertradename2', 'othertradename3', 'othertradename4', 'dcagent1', 'dcagent2', 'dcagentcity', 'dcagentstate', 'alternateagent1', 'alternateagent2', 'alternateagentcity', 'alternateagentstate'])
#r = telecom_efficient_search(input("type a searchterm:  "), ['carriername', 'businessname', 'holdingcompany', 'othertradename1', 'othertradename2', 'othertradename3', 'othertradename4', 'dcagent1', 'dcagent2', 'dcagentcity', 'dcagentstate', 'alternateagent1', 'alternateagent2', 'alternateagentcity', 'alternateagentstate'])
#r = telecom_search(input("type a searchterm:  "), ['carriername', 'businessname', 'holdingcompany', 'othertradename1', 'othertradename2', 'othertradename3', 'othertradename4', 'dcagent1', 'dcagent2', 'dcagentcity', 'dcagentstate'])
#pp.pprint(f"high: {r[0]}")
#print(coll_tel.find_one({"id":82}))


# iter_result = "".join(list(map(lambda x: f"""<a href="/locations/{'-'.join(x['statename'].split(' '))}">{x['statename'].title()}</a>""", coll_st.find())))

# print(iter_result)

def render_xml_sitemap(s, t, rt):
    sitemap_urls = []
    for z in trange(len(s["pages"]), bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.RED, Fore.RESET)):
        i = s["pages"][z]
        #for i in s["pages"]:
        if re.search(r'^/locations/', i["route"]) is not None:
            if len(i["route"].split("/")) == 3:
                sitemap_urls.append("".join(list(map(lambda n: f"""<url><loc>https://www.{s["sitename"]}.com/locations/{n['statename']}</loc></url>""", coll_st.find()))))
            elif len(i["route"].split("/")) == 5:
                sitemap_urls.append("".join(list(map(lambda n: f"""<url><loc>https://www.{s["sitename"]}.com/locations/{n['statename']}/{n['countyname']}-{n['countyid']}/{n['cityname']}-{n['id']}</loc></url>""", coll_ci.find()))))
        elif re.search(r'^/blog/', i["route"]) is not None:
            if len(i["route"].split("/")) == 3:
                sitemap_urls.append(f"""<url><loc>https://www.{s["sitename"]}.com{i["route"]}</loc></url>""")
            elif len(i["route"].split("/")) == 4:
                sitemap_urls.append("".join(list(map(lambda n: f"""<url><loc>https://www.{s["sitename"]}.com/blog/posts/{n['bloguri'] if n['bloguri'] else ""}-{n['id']}</loc></url>""", coll_bl.find({'blogcategory': s["blogcategory"]})))))
        elif re.search(r'^/registered-agents/', i["route"]) is not None:
            if re.search(r'^/registered-agents/search', i["route"]) is not None:
                import urllib.parse
                for n in ["company", "agency", "state", "city"]:
                    sitemap_urls.append("".join(list(map(lambda k: "".join([f"""<url><loc>https://www.{s["sitename"]}.com""", urllib.parse.quote(f"""/registered-agents/search/{n}/{k.lower()}"""), "</loc></url>"]), coll_ra.find().distinct(n)))))
            else:
                sitemap_urls.append("".join(list(map(lambda n: f"""<url><loc>https://www.{s["sitename"]}.com/registered-agents/{n['id']}</loc></url>""", coll_ra.find()))))
        elif re.search(r'^/telecom-agents/', i["route"]) is not None:
            if re.search(r'^/telecom-agents/search', i["route"]) is not None:
                import urllib.parse
                for n in ['carriername', 'businessname', 'holdingcompany', 'othertradename1', 'othertradename2', 'othertradename3', 'othertradename4', 'dcagent1', 'dcagent2', 'dcagentcity', 'dcagentstate']:
                    sitemap_urls.append("".join(list(map(lambda k: "".join([f"""<url><loc>https://www.{s["sitename"]}.com""", urllib.parse.quote(f"""/telecom-agents/search/{n}/{k.lower()}"""), "</loc></url>"]), coll_tel.find().distinct(n)))))
            else:
                sitemap_urls.append("".join(list(map(lambda n: f"""<url><loc>https://www.{s["sitename"]}.com/telecom-agents/{n['id']}</loc></url>""", coll_tel.find()))))
        elif re.search(r'^/process-server/', i["route"]) is not None:
            if re.search(r'^/process-server/id/state/city', i["route"]) is not None:
                # nested map lambda functions to get all three layers of permutated dynamic url routes simultaneously
                sitemap_urls.append("".join(list(map(lambda n: "".join([f"""<url><loc>https://www.{s["sitename"]}.com/process-server/{"-".join(n['name'].split(" ")).lower()}-{n['id']}</loc></url>""", "".join(list(map(lambda k: "".join([f"""<url><loc>https://www.{s["sitename"]}.com/process-server/{"-".join(n['name'].split(" ")).lower()}-{n['id']}/{"-".join(k.split(" ")).lower()}</loc></url>""", "".join(list(map(lambda m: f"""<url><loc>https://www.{s["sitename"]}.com/process-server/{"-".join(n['name'].split(" ")).lower()}-{n['id']}/{"-".join(k.split(" ")).lower()}/{"-".join(m.split(" ")).lower()}</loc></url>""", coll_ra.find({'state': k}).distinct('city'))))]), coll_ra.find().distinct("state"))))]), coll_cp.find()))))
        else:
            if re.search(r'\.[a-z]{2,4}$', i["route"]) is None:
                sitemap_urls.append(f"""<url><loc>https://www.{s["sitename"]}.com{i["route"]}</loc></url>""")
    sitemap = "".join(["""<?xml version="1.0" encoding="utf-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">""", "".join(sitemap_urls), """</urlset>"""])
    return sitemap

pp.pprint(render_xml_sitemap(coll_si.find_one({"id": 7}), coll_te.find_one({"id": 5}), "/sitemap.xml")[0:1000])

