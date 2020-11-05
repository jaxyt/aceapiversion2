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

def registered_agent_search(k, q):
    res = []
    query = re.compile(q, re.IGNORECASE)
    for i in coll_ra.find({k: query}):
        res.append(i)
    return res

def no_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def text_score_search(arr):
    res = []
    k = arr[3]
    q = re.sub(r"[^A-z0-9\s]+", "", arr[4])
    qu = "("+re.sub(r"\s+", ")|(", q.strip())+")"
    query = re.compile(qu, re.IGNORECASE)
    for i in coll_ra.aggregate([{"$match": {"$or" : [{"company": query},{"agency": query},{"state": query},{"city": query}]}},{"$sort": { k: 1 }}]):
        res.append(i)
    return sort_results(res, q)

def sort_results(results, quer):
    scores = []
    sorted_scores = []
    for val in results:
        avg_cnt = 0
        if val['company']:
            avg_cnt += 1
        if val['agency']:
            avg_cnt += 1
        if val['state']:
            avg_cnt += 1
        if val['city']:
            avg_cnt += 1
        scores.append({"obj": val, "averagescore": (similar_text(val['company'], quer)+similar_text(val['agency'], quer)+similar_text(val['state'], quer)+similar_text(val['city'], quer))/4, "scorearr": [similar_text(val['company'], quer), similar_text(val['agency'], quer), similar_text(val['state'], quer), similar_text(val['city'], quer)]})
    for val in scores:
        if len(sorted_scores) == 0:
            sorted_scores.append(val)
        else:
            for idx, n in enumerate(sorted_scores):
                if val['averagescore'] > n['averagescore']:
                    sorted_scores.insert(idx, val)
                    break
                elif idx == len(sorted_scores) - 1 and val['averagescore'] < n['averagescore']:
                    sorted_scores.append(val)
                    break
                elif val['averagescore'] == n['averagescore']:
                    if max(val['scorearr']) > max(n['scorearr']):
                        sorted_scores.insert(idx, val)
                        break
    return sorted_scores


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

def ra_search(searchterm):
    results = {}
    agents = list(map(add_to_map, coll_ra.find()))
    for i in agents:
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
        similarities = [cosine_sim_vectors(vectors[0], k) for k in vectors[1:]]
        """for k in vectors[1:]:
            similarities.append(cosine_sim_vectors(vectors[0], k))"""
        #max_similarity = max(similarities)
        avg_similarity = sum(similarities)/(len(similarities) + 1)
        results[f"{i['id']}"] = avg_similarity
    return [coll_ra.find_one({'id': int(m[0])}) for m in sorted(results.items(), key=lambda x: x[1], reverse=True) if m[1]]


def compiler_v3(s, t, r, arr):
    page = ""
    spage = None
    tpage = None
    if arr[1] == "locations":
        if len(arr) == 3:
            page = "/locations/state"
        elif len(arr) == 4:
            page = "/locations/state/county"
        elif len(arr) == 5:
            page = "/locations/state/county/city"
    elif arr[1] == "blog":
        if len(arr) == 3:
            page = "/blog/posts"
        elif len(arr) == 4:
            page = "/blog/posts/id"
    elif arr[1] == "registered-agents":
        if len(arr) == 3:
            page = "/registered-agents/id"
        elif len(arr) == 5:
            page = "/registered-agents/search/key/value"
    elif arr[1] == "process-server":
        if len(arr) == 3:
            page = "/process-server/id"
        elif len(arr) == 4:
            page = "/process-server/id/state"
        elif len(arr) == 5:
            page = "/process-server/id/state/city"
    elif arr[1] == "agents-by-state":
        if len(arr) == 2:
            page = "/agents-by-state"
        elif len(arr) == 3:
            page = "/agents-by-state/state"
        elif len(arr) == 4:
            page = "/agents-by-state/state/city"
    elif arr[1] == "telecom-agents":
        if len(arr) == 3:
            page = "/telecom-agents/id"
        elif len(arr) == 5:
            page = "/telecom-agents/search/key/value"
    else:
        page = r
    for i in s.pages:
        if i.route == page:
            spage = i
    for i in t.pages:
        if i.route == page:
            tpage = i
    states_links = "".join(["""<div class="states-links">""", "".join(list(map(lambda x: f"""<a href="/locations/{'-'.join(x['statename'].split(' '))}">{x['statename'].title()}</a>""", coll_st.find()))), "</div>"])
    comp = f"""<!DOCTYPE html><html lang="en"><head>{s.sitemetas if s.sitemetas else t.sitemetas if t.sitemetas else ""}{spage.pagemetas if spage.pagemetas else tpage.pagemetas if tpage.pagemetas else ""}{s.sitelinks if s.sitelinks else t.sitelinks if t.sitelinks else ""}{spage.pagelinks if spage.pagelinks else tpage.pagelinks if tpage.pagelinks else ""}<title>{spage.title if spage.title else tpage.title if tpage.title else ""}</title>{spage.pagestyle if spage.pagestyle else s.sitestyle if s.sitestyle else tpage.pagestyle if tpage.pagestyle else t.sitestyle if t.sitestyle else ""}</head><body>{spage.pageheader if spage.pageheader else s.siteheader if s.siteheader else tpage.pageheader if tpage.pageheader else t.siteheader if t.siteheader else ""}{spage.content if spage.content else tpage.content if tpage.content else ""}{spage.pagefooter if spage.pagefooter else s.sitefooter if s.sitefooter else tpage.pagefooter if tpage.pagefooter else t.sitefooter if t.sitefooter else ""}{s.sitescripts if s.sitescripts else t.sitescripts if t.sitescripts else ""}{spage.pagescripts if spage.pagescripts else tpage.pagescripts if tpage.pagescripts else ""}</body></html>"""
    
    site_state = coll_st.find_one({'id': s.location.stateid})
    site_state_acronym = site_state['stateacronym']
    site_counties_links = "".join(["""<div class="link-list">""", "".join(list(map(lambda x: f"""<a class="location-link" href="/locations/{x['statename']}/{x['countyname']}-{x['id']}">{x['countyname'].title()}</a>""", coll_co.find({'stateid': site_state['id']})))), """</div>"""])
    
    comp = re.sub(r'XXsitestateXX', site_state['statename'].title(), comp)
    comp = re.sub(r"XXsitestateacronymXX", site_state_acronym, comp)
    comp = re.sub(r'XXsitecountylinksXX', site_counties_links, comp)
    
    site_county = coll_co.find_one({'id': s.location.countyid})
    site_cities_links = "".join(["""<div class="link-list">""", "".join(list(map(lambda x: f"""<a class="location-link" href="/locations/{x['statename']}/{x['countyname']}-{x['countyid']}/{x['cityname']}-{x['id']}">{x['cityname'].title()}</a>""", coll_ci.find({'countyid': site_county['id']})))), """</div>"""])
    
    comp = re.sub(r'XXsitecountyXX', site_county['countyname'].title(), comp)
    comp = re.sub(r'XXsitecitylinksXX', site_cities_links, comp)

    site_city = coll_ci.find_one({'id': s.location.cityid})
    comp = re.sub(r'XXsitecityXX', site_city['cityname'].title(), comp)
    comp = re.sub(r'XXstateslinksXX', states_links, comp)
    if arr[1] == "locations":
        if len(arr) >= 3:
            page_state = coll_st.find_one({'statename': " ".join(arr[2].split('-'))})
            page_state_acronym = page_state['stateacronym']
            page_counties_links = "".join(["""<div class="link-list">""", "".join(list(map(lambda x: f"""<a class="location-link" href="/locations/{x['statename']}/{x['countyname']}-{x['id']}">{x['countyname'].title()}</a>""", coll_co.find({'stateid': page_state['id']})))), """</div>"""])
            
            comp = re.sub(r'XXpagestateXX', page_state['statename'].title(), comp)
            comp = re.sub(r'XXpagestateacronymXX', page_state_acronym, comp)
            comp = re.sub(r'XXpagecountylinksXX', page_counties_links, comp)
            if len(arr) >= 4:
                page_county = coll_co.find_one({'id': int(arr[3].split("-")[-1])})
                page_cities_links = "".join(["""<div class="link-list">""", "".join(list(map(lambda x: f"""<a class="location-link" href="/locations/{x['statename']}/{x['countyname']}-{x['countyid']}/{x['cityname']}-{x['id']}">{x['cityname'].title()}</a>""", coll_ci.find({'countyid': page_county['id']})))), """</div>"""])
                
                comp = re.sub(r'XXpagecountyXX', page_county['countyname'].title(), comp)
                comp = re.sub(r'XXpagecitylinksXX', page_cities_links, comp)
                if len(arr) == 5:
                    page_city = coll_ci.find_one({'id': int(arr[4].split("-")[-1])})
                    comp = re.sub(r'XXpagecityXX', page_city['cityname'].title(), comp)
    elif arr[1] == "blog":
        if len(arr) == 3:
            snippets = """<div class="snippets">"""
            for i in coll_bl.find({'blogcategory': s.blogcategory}):
                post = ""
                if s.national == False:
                    post_content = no_html_tags(i['blogpost'])
                    if len(post_content) > 100:
                        post = post_content[0:100]+"..."
                    else:
                        post = post_content+"..."
                else:
                    post_content = no_html_tags(i['blogpostnational'])
                    if len(post_content) > 100:
                        post = post_content[0:100]+"..."
                    else:
                        post = post_content+"..."
                snippets += f"""<div class="snippet"><h3><a href="/blog/posts/{"-".join(i['bloguri'].split(" "))}-{i['id']}">{i['blogtitle'].title()}</a></h3><p>{post}</p></div>"""
            snippets += "</div>"
            comp = re.sub('XXsnippetsXX', snippets, comp)
        elif len(arr) == 4:
            blog_post = coll_bl.find_one({'id': int(arr[3].split('-')[-1])})
            post = ""
            if s.national == False:
                post = blog_post['blogpost']
            else:
                post = blog_post['blogpostnational']
            post_template = f"""<div class="blog-post"><h1>{blog_post['blogtitle'].title()}</h1><div><span>{blog_post['blogdate']}</span><br><span>{blog_post['blogauthor']}</span></div><p>{post}</p></div>"""
            comp = re.sub('XXblogpostXX', post_template, comp)
            comp = re.sub('XXblogtitleXX', blog_post['blogtitle'] if blog_post['blogtitle'] else "", comp)
            comp = re.sub('XXbloguriXX', blog_post['bloguri'] if blog_post['bloguri'] else "", comp)
            comp = re.sub('XXblogcategoryXX', blog_post['blogcategory'] if blog_post['blogcategory'] else "", comp)
            comp = re.sub('XXblogkeywordsXX', blog_post['blogkeywords'] if blog_post['blogkeywords'] else "", comp)
            comp = re.sub('XXblogpostlocalXX', blog_post['blogpost'] if blog_post['blogpost'] else "", comp)
            comp = re.sub('XXblogpostnationalXX', blog_post['blogpostnational'] if blog_post['blogpostnational'] else "", comp)
            comp = re.sub('XXblogauthorXX', blog_post['blogauthor'] if blog_post['blogauthor'] else "", comp)
    elif arr[1] == "registered-agents":
        if len(arr) == 3:
            agent = coll_ra.find_one({'id': int(arr[2].split("-")[-1])})
            agent_info = "".join([
                f"""<div class="registered-agent"><ul id="{agent['id']}" class="agent-container">""",
                f"""<li class="company">Company:&nbsp;<a href="/registered-agents/search/company/{agent['company']}">{agent['company'].title()}</a></li>""" if agent['company'] else "",
                f"""<li class="agency">Agent:&nbsp;<a href="/registered-agents/search/agency/{agent['agency']}">{agent['agency'].title()}</a></li>""" if agent['agency'] else "",
                f"""<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{agent['state']}">{agent['state'].title()}</a></li>""" if agent['state'] else "",
                f"""<li class="city">City:&nbsp;<a href="/registered-agents/search/city/{agent['city']}, {agent['state']}">{agent['city'].title()}</a></li>""" if agent['city'] and agent['state'] else "",
                f"""<li class="contact-point">Contact:&nbsp;{agent['contact'].title()}</li>""" if agent['contact'] else "",
                f"""<li class="address">Address:&nbsp;{agent['address'].title()}</li>""" if agent['address'] else "",
                f"""<li class="mail">Mailing Address:&nbsp;{agent['mail'].title()}</li>"""  if agent['mail'] else "",
                f"""<li class="ra-phone">Phone:&nbsp;{agent['phone'].title()}</li>""" if agent['phone'] else "",
                f"""<li class="fax">Fax:&nbsp;{agent['fax'].title()}</li>""" if agent['fax'] else "",
                f"""<li class="email">Email:&nbsp;{agent['email'].title()}</li>""" if agent['email'] else "",
                f"""<li class="website">Website:&nbsp;{agent['website'].title()}</li>""" if agent['website'] else "",
                "</ul></div>"
            ])
            comp = re.sub("XXagentXX", agent_info, comp)
            comp = re.sub("XXagentagencyXX", f"""{agent['agency'].title() if agent['agency'] else ""}""", comp)
            comp = re.sub("XXagentcompanyXX", f"""{agent['company'].title() if agent['company'] else ""}""", comp)
            comp = re.sub("XXagentstateXX", f"""{agent['state'].title() if agent['state'] else ""}""", comp)
            comp = re.sub("XXagentcityXX", f"""{agent['city'].title() if agent['city'] else ""}""", comp)
            comp = re.sub("XXcorpXX", f"""{agent['company'].title() if agent['company'] else agent['agency'].title() if agent['agency'] else ""}""", comp)
            if agent['state']:
                rege = re.compile(agent['state'], re.IGNORECASE)
                agent_state = coll_st.find_one({"statename": rege})
                state_acronym = agent_state['stateacronym']
                comp = re.sub(r"XXstateacronymXX", state_acronym, comp)
            else:
                comp = re.sub(r"XXstateacronymXX", "", comp)
        elif len(arr) == 5:
            from urllib.parse import unquote
            from .tests2 import lev_and_cos_search
            agents_info = """<div class="registered-agents">"""
            k = arr[3]
            q = unquote(arr[4])
            q = re.sub(r'[^\w\s]','',q)
            q = re.sub(r'\s{2,}','',q)
            q = q.strip(" ")
            search_results = lev_and_cos_search(q)
            for m in search_results[0:50]:
                current_agent = coll_ra.find_one({'id': int(m[0])})
                slug = slugify(f"""{current_agent['company'] if current_agent['company'] else (current_agent['agency'] if current_agent['agency'] else "")}-service-of-process-{current_agent['id']}""")
                agents_info += "".join([
                    f"""<ul id="{current_agent['id']}" class="agent-container">""",
                    f"""<li class="company">Agency:&nbsp;<a href="/registered-agents/search/company/{current_agent['company']}">{current_agent['company'].title()}</a></li>""" if current_agent['company'] else "",
                    f"""<li class="agency">{"Alt-Name" if current_agent["company"] else "Agency"}:&nbsp;<a href="/registered-agents/search/agency/{current_agent['agency']}">{current_agent['agency'].title()}</a></li>""" if current_agent['agency'] else "",
                    f"""<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{current_agent['state']}">{current_agent['state'].title()}</a></li>""" if current_agent['state'] else "",
                    f"""<li class="city">City:&nbsp;<a href="/registered-agents/search/city/{current_agent['city']}, {current_agent['state']}">{current_agent['city'].title()}</a></li>""" if current_agent['city'] and current_agent['state'] else "",
                    f"""<li class="address">Address:&nbsp;{current_agent['address'].title()}</li>""" if current_agent['address'] else "",
                    f"""<li class="agent-details"><a href="/registered-agents/{slug}"><button>Go to Details</button></a></li>""",
                    "</ul>"
                ])
            agents_info += "</div>"
            comp = re.sub("XXagentsXX", agents_info, comp)
            comp = re.sub("XXagentsqueryXX", arr[4].title(), comp)
            #f"""<li class="contact-point">Contact:&nbsp;{i['contact'].title()}</li>""" if i['contact'] else "",
            #f"""<li class="mail">Mailing Address:&nbsp;{i['mail'].title()}</li>""" if i['mail'] else "",
            #f"""<li class="ra-phone">Phone:&nbsp;{i['phone'].title()}</li>""" if i['phone'] else "",
            #f"""<li class="fax">Fax:&nbsp;{i['fax'].title()}</li>""" if i['fax'] else "",
            #f"""<li class="email">Email:&nbsp;{i['email'].title()}</li>""" if i['email'] else "",
            #f"""<li class="website">Website:&nbsp;{i['website'].title()}</li>""" if i['website'] else "",
    elif arr[1] == "process-server":
        if len(arr) == 3:
            agents_info = """<div class="registered-agents">"""
            corp = coll_cp.find_one({'id': int(arr[2].split("-")[-1])})
            k = corp['searchkey']
            q = corp['searchvalue']
            query = re.compile(q, re.IGNORECASE)
            for i in coll_ra.find({k: query}):
                slug = slugify(f"""{i['company'] if i['company'] else (i['agency'] if i['agency'] else "")}-service-of-process-{i['id']}""")
                agents_info += "".join([
                    f"""<ul id="{i['id']}" class="agent-container">""",
                    f"""<li class="company">Company:&nbsp;<a href="/registered-agents/search/company/{i['company']}">{i['company'].title()}</a></li>""" if i['company'] else "",
                    f"""<li class="agency">Agent:&nbsp;<a href="/registered-agents/search/agency/{i['agency']}">{i['agency'].title()}</a></li>""" if i['agency'] else "",
                    f"""<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{i['state']}">{i['state'].title()}</a></li>""" if i['state'] else "",
                    f"""<li class="city">City:&nbsp;<a href="/registered-agents/search/city/{i['city']}, {i['state']}">{i['city'].title()}</a></li>""" if i['city'] and {i['state']} else "",
                    f"""<li class="contact-point">Contact:&nbsp;{i['contact'].title()}</li>""" if i['contact'] else "",
                    f"""<li class="address">Address:&nbsp;{i['address'].title()}</li>""" if i['address'] else "",
                    f"""<li class="mail">Mailing Address:&nbsp;{i['mail'].title()}</li>""" if i['mail'] else "",
                    f"""<li class="ra-phone">Phone:&nbsp;{i['phone'].title()}</li>""" if i['phone'] else "",
                    f"""<li class="fax">Fax:&nbsp;{i['fax'].title()}</li>""" if i['fax'] else "",
                    f"""<li class="email">Email:&nbsp;{i['email'].title()}</li>""" if i['email'] else "",
                    f"""<li class="website">Website:&nbsp;{i['website'].title()}</li>""" if i['website'] else "",
                    f"""<li class="agent-details"><a href="/registered-agents/{slug}"><button>Go to Details</button></a></li>""",
                    "</ul>"
                ])
            agents_info += "</div>"
            comp = re.sub('XXagentsXX', agents_info, comp)
            comp = re.sub('XXcorpXX', corp['name'], comp)
            corps_in_states = """<div class="process-server-corp-state-links">"""
            for i in coll_st.find():
                corps_in_states += f"""<a href="{"/".join(arr)}/{"-".join(i['statename'].split(" "))}">{i['statename'].title()}</a>"""
            corps_in_states += """</div>"""
            comp = re.sub('XXcorpsinstatesXX', corps_in_states, comp)
        elif len(arr) == 4:
            agents_info = """<div class="registered-agents">"""
            corp = coll_cp.find_one({'id': int(arr[2].split("-")[-1])})
            st = " ".join(arr[3].split("-"))
            k = corp['searchkey']
            q = corp['searchvalue']
            query = re.compile(q, re.IGNORECASE)
            state_query = re.compile(st.lower(), re.IGNORECASE)
            for i in coll_ra.find({k: query, 'state': state_query}):
                slug = slugify(f"""{i['company'] if i['company'] else (i['agency'] if i['agency'] else "")}-service-of-process-{i['id']}""")
                agents_info += "".join([
                    f"""<ul id="{i['id']}" class="agent-container">""",
                    f"""<li class="company">Company:&nbsp;<a href="/registered-agents/search/company/{i['company']}">{i['company'].title()}</a></li>""" if i['company'] else "",
                    f"""<li class="agency">Agent:&nbsp;<a href="/registered-agents/search/agency/{i['agency']}">{i['agency'].title()}</a></li>""" if i['agency'] else "",
                    f"""<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{i['state']}">{i['state'].title()}</a></li>""" if i['state'] else "",
                    f"""<li class="city">City:&nbsp;<a href="/registered-agents/search/city/{i['city']}, {i['state']}">{i['city'].title()}</a></li>""" if i['city'] and {i['state']} else "",
                    f"""<li class="contact-point">Contact:&nbsp;{i['contact'].title()}</li>""" if i['contact'] else "",
                    f"""<li class="address">Address:&nbsp;{i['address'].title()}</li>""" if i['address'] else "",
                    f"""<li class="mail">Mailing Address:&nbsp;{i['mail'].title()}</li>""" if i['mail'] else "",
                    f"""<li class="ra-phone">Phone:&nbsp;{i['phone'].title()}</li>""" if i['phone'] else "",
                    f"""<li class="fax">Fax:&nbsp;{i['fax'].title()}</li>""" if i['fax'] else "",
                    f"""<li class="email">Email:&nbsp;{i['email'].title()}</li>""" if i['email'] else "",
                    f"""<li class="website">Website:&nbsp;{i['website'].title()}</li>""" if i['website'] else "",
                    f"""<li class="agent-details"><a href="/registered-agents/{slug}"><button>Go to Details</button></a></li>""",
                    "</ul>"
                ])
            agents_info += "</div>"
            comp = re.sub('XXagentsXX', agents_info, comp)
            comp = re.sub('XXcorpXX', corp['name'], comp)
            comp = re.sub('XXstatequeryXX', st.title(), comp)
            corps_in_cities = """<div class="process-server-corps-city-links">"""
            for i in coll_ra.find({k: query, 'state': state_query}).distinct('city'):
                corps_in_cities += f"""<a href="{"/".join(arr)}/{"-".join(i.lower().split(" "))}">{i.title()}</a>""" if i else ""
            corps_in_cities += """</div>"""
            comp = re.sub('XXcitycorpsXX', corps_in_cities, comp)
        elif len(arr) == 5:
            agents_info = """<div class="registered-agents">"""
            corp = coll_cp.find_one({'id': int(arr[2].split("-")[-1])})
            st = " ".join(arr[3].split("-"))
            cit = " ".join(arr[4].split("-"))
            k = corp['searchkey']
            q = corp['searchvalue']
            query = re.compile(q, re.IGNORECASE)
            state_query = re.compile(st.lower(), re.IGNORECASE)
            city_query = re.compile(cit.lower(), re.IGNORECASE)
            for i in coll_ra.find({k: query, 'state': state_query, 'city': city_query}):
                slug = slugify(f"""{i['company'] if i['company'] else (i['agency'] if i['agency'] else "")}-service-of-process-{i['id']}""")
                agents_info += "".join([
                    f"""<ul id="{i['id']}" class="agent-container">""",
                    f"""<li class="company">Company:&nbsp;<a href="/registered-agents/search/company/{i['company']}">{i['company'].title()}</a></li>""" if i['company'] else "",
                    f"""<li class="agency">Agent:&nbsp;<a href="/registered-agents/search/agency/{i['agency']}">{i['agency'].title()}</a></li>""" if i['agency'] else "",
                    f"""<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{i['state']}">{i['state'].title()}</a></li>""" if i['state'] else "",
                    f"""<li class="city">City:&nbsp;<a href="/registered-agents/search/city/{i['city']}, {i['state']}">{i['city'].title()}</a></li>""" if i['city'] and {i['state']} else "",
                    f"""<li class="contact-point">Contact:&nbsp;{i['contact'].title()}</li>""" if i['contact'] else "",
                    f"""<li class="address">Address:&nbsp;{i['address'].title()}</li>""" if i['address'] else "",
                    f"""<li class="mail">Mailing Address:&nbsp;{i['mail'].title()}</li>""" if i['mail'] else "",
                    f"""<li class="ra-phone">Phone:&nbsp;{i['phone'].title()}</li>""" if i['phone'] else "",
                    f"""<li class="fax">Fax:&nbsp;{i['fax'].title()}</li>""" if i['fax'] else "",
                    f"""<li class="email">Email:&nbsp;{i['email'].title()}</li>""" if i['email'] else "",
                    f"""<li class="website">Website:&nbsp;{i['website'].title()}</li>""" if i['website'] else "",
                    f"""<li class="agent-details"><a href="/registered-agents/{slug}"><button>Go to Details</button></a></li>""",
                    "</ul>"
                ])
            agents_info += "</div>"
            comp = re.sub('XXagentsXX', agents_info, comp)
            comp = re.sub('XXcorpXX', corp['name'], comp)
            comp = re.sub('XXstatequeryXX', st.title(), comp)
            comp = re.sub('XXcityqueryXX', cit.title(), comp)
    elif arr[1] == "agents-by-state":
        if len(arr) == 2:
            corps_in_states = """<div class="state-corps-links">"""
            for i in coll_st.find():
                corps_in_states += f"""<a href="/agents-by-state/{"-".join(i['statename'].split(" "))}">{i['statename'].title()}</a>"""
            corps_in_states += """</div>"""
            comp = re.sub('XXcorpsinstatesXX', corps_in_states, comp)
        elif len(arr) == 3:
            agents_info = """<div class="registered-agents">"""
            st = " ".join(arr[2].split("-"))
            state_query = re.compile(st.lower(), re.IGNORECASE)
            for i in coll_ra.find({'state': state_query}):
                slug = slugify(f"""{i['company'] if i['company'] else (i['agency'] if i['agency'] else "")}-service-of-process-{i['id']}""")
                agents_info += "".join([
                    f"""<ul id="{i['id']}" class="agent-container">""",
                    f"""<li class="company">Agent:&nbsp;<a href="/registered-agents/search/company/{i['company']}">{i['company'].title()}</a></li>""" if i['company'] else "",
                    f"""<li class="agency">{"Alt-Name" if i['company'] else "Agent"}:&nbsp;<a href="/registered-agents/search/agency/{i['agency']}">{i['agency'].title()}</a></li>""" if i['agency'] else "",
                    f"""<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{i['state']}">{i['state'].title()}</a></li>""" if i['state'] else "",
                    f"""<li class="city">City:&nbsp;<a href="/registered-agents/search/city/{i['city']}, {i['state']}">{i['city'].title()}</a></li>""" if i['city'] and {i['state']} else "",
                    f"""<li class="contact-point">Contact:&nbsp;{i['contact'].title()}</li>""" if i['contact'] else "",
                    f"""<li class="address">Address:&nbsp;{i['address'].title()}</li>""" if i['address'] else "",
                    f"""<li class="mail">Mailing Address:&nbsp;{i['mail'].title()}</li>""" if i['mail'] else "",
                    f"""<li class="ra-phone">Phone:&nbsp;{i['phone'].title()}</li>""" if i['phone'] else "",
                    f"""<li class="fax">Fax:&nbsp;{i['fax'].title()}</li>""" if i['fax'] else "",
                    f"""<li class="email">Email:&nbsp;{i['email'].title()}</li>""" if i['email'] else "",
                    f"""<li class="website">Website:&nbsp;{i['website'].title()}</li>""" if i['website'] else "",
                    f"""<li class="agent-details"><a href="/registered-agents/{slug}"><button>Go to Details</button></a></li>""",
                    "</ul>"
                ])
            agents_info += "</div>"
            comp = re.sub('XXagentsXX', agents_info, comp)
            comp = re.sub('XXstatequeryXX', st.title(), comp)
            corps_in_cities = """<div class="corps-in-city-links">"""
            for i in coll_ra.find({'state': state_query}).distinct('city'):
                corps_in_cities += f"""<a href="{"/".join(arr)}/{"-".join(i.lower().split(" "))}">{i.title()}</a>""" if i else ""
            corps_in_cities += """</div>"""
            comp = re.sub('XXcitycorpsXX', corps_in_cities, comp)
        elif len(arr) == 4:
            agents_info = """<div class="registered-agents">"""
            st = " ".join(arr[2].split("-"))
            cit = " ".join(arr[3].split("-"))
            state_query = re.compile(st.lower(), re.IGNORECASE)
            city_query = re.compile(cit.lower(), re.IGNORECASE)
            for i in coll_ra.find({'state': state_query, 'city': city_query}):
                slug = slugify(f"""{i['company'] if i['company'] else (i['agency'] if i['agency'] else "")}-service-of-process-{i['id']}""")
                agents_info += "".join([
                    f"""<ul id="{i['id']}" class="agent-container">""",
                    f"""<li class="company">Agent:&nbsp;<a href="/registered-agents/search/company/{i['company']}">{i['company'].title()}</a></li>""" if i['company'] else "",
                    f"""<li class="agency">{"Alt-Name" if i['company'] else "Agent"}:&nbsp;<a href="/registered-agents/search/agency/{i['agency']}">{i['agency'].title()}</a></li>""" if i['agency'] else "",
                    f"""<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{i['state']}">{i['state'].title()}</a></li>""" if i['state'] else "",
                    f"""<li class="city">City:&nbsp;<a href="/registered-agents/search/city/{i['city']}, {i['state']}">{i['city'].title()}</a></li>""" if i['city'] and {i['state']} else "",
                    f"""<li class="contact-point">Contact:&nbsp;{i['contact'].title()}</li>""" if i['contact'] else "",
                    f"""<li class="address">Address:&nbsp;{i['address'].title()}</li>""" if i['address'] else "",
                    f"""<li class="mail">Mailing Address:&nbsp;{i['mail'].title()}</li>""" if i['mail'] else "",
                    f"""<li class="ra-phone">Phone:&nbsp;{i['phone'].title()}</li>""" if i['phone'] else "",
                    f"""<li class="fax">Fax:&nbsp;{i['fax'].title()}</li>""" if i['fax'] else "",
                    f"""<li class="email">Email:&nbsp;{i['email'].title()}</li>""" if i['email'] else "",
                    f"""<li class="website">Website:&nbsp;{i['website'].title()}</li>""" if i['website'] else "",
                    f"""<li class="agent-details"><a href="/registered-agents/{slug}"><button>Go to Details</button></a></li>""",
                    "</ul>"
                ])
            agents_info += "</div>"
            comp = re.sub('XXagentsXX', agents_info, comp)
            comp = re.sub('XXstatequeryXX', st.title(), comp)
            comp = re.sub('XXcityqueryXX', cit.title(), comp)
    elif arr[1] == "telecom-agents":
        
        if len(arr) == 3:
            agent = coll_tel.find_one({'id': int(arr[2].split("-")[-1])})
            agent_info = "".join([
                f"""<div class="registered-agent"><ul id="{agent['id']}" class="agent-container">""",
                f"""<li class="carriername">Carrier:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['carriername'])}">{agent['carriername'] if agent['carriername'] else ""}</a></li>""",
                f"""<li class="businessname">Business Name:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['businessname'])}">{agent['businessname'] if agent['businessname'] else ""}</a></li>""",
                f"""<li class="holdingcompany">Holding Company:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['holdingcompany'])}">{agent['holdingcompany'] if agent['holdingcompany'] else ""}</a></li>""",
                f"""<li class="hqaddress">HQ Address:&nbsp;{agent['hqaddress1'] if agent['hqaddress1'] else ""}{", "+agent['hqaddress2'] if agent['hqaddress2'] else ""}{", "+agent['hqaddress3'] if agent['hqaddress3'] else ""}</li>""",
                f"""<li class="othertradenames"><ul class="other-trade-names">Other Trade Names""" if agent['othertradename1'] else "",
                f"""<li class="othertradenames1"><a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['othertradename1'])}">{agent['othertradename1']}</a></li>""" if agent['othertradename1'] else "",
                f"""<li class="othertradenames2"><a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['othertradename2'])}">{agent['othertradename2']}</a></li>""" if agent['othertradename2'] else "",
                f"""<li class="othertradenames3"><a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['othertradename3'])}">{agent['othertradename3']}</a></li>""" if agent['othertradename3'] else "",
                f"""<li class="othertradenames4"><a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['othertradename4'])}">{agent['othertradename4']}</a></li>""" if agent['othertradename4'] else "",
                f"""</ul></li>""" if agent['othertradename1'] else "",
                f"""<li class="dcagents"><ul class="dc-agents">DC Agents""" if agent['dcagent1'] else "",
                f"""<li class="dcagent1">Agent:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['dcagent1'])}">{agent['dcagent1']}</a></li>""" if agent['dcagent1'] else "",
                f"""<li class="dcagent2">Agent Two:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['dcagent2'])}">{agent['dcagent2']}</a></li>""" if agent['dcagent2'] else "",
                f"""<li class="dcagentaddress">Address:&nbsp;{agent['dcagentaddress1']}{", "+agent['dcagentaddress2'] if agent['dcagentaddress2'] else ""}{", "+agent['dcagentaddress3'] if agent['dcagentaddress3'] else ""}</li>""" if agent['dcagentaddress1'] else "",
                f"""</ul></li>""" if agent['dcagent1'] else "",
                f"""<li class="alternateagents"><ul class="alternate-agents">Alternate Agents""" if agent['alternateagent1'] else "",
                f"""<li class="alternateagent1">Alt Agent:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['alternateagent1'])}">{agent['alternateagent1']}</a></li>""" if agent['alternateagent1'] else "",
                f"""<li class="alternateagent2">Alt Agent:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['alternateagent2'])}">{agent['alternateagent2']}</a></li>""" if agent['alternateagent2'] else "",
                f"""<li class="alternateagenttelephone">Phone:&nbsp;{agent['alternateagenttelephone']}</li>""" if agent['alternateagenttelephone'] else "",
                f"""<li class="alternateagentext">Ext:&nbsp;{agent['alternateagentext']}</li>""" if agent['alternateagentext'] else "",
                f"""<li class="alternateagentfax">Fax:&nbsp;{agent['alternateagentfax']}</li>""" if agent['alternateagentfax'] else "",
                f"""<li class="alternateagentemail">Email:&nbsp;{agent['alternateagentemail']}</li>""" if agent['alternateagentemail'] else "",
                f"""<li class="alternateagentaddress">Address:&nbsp;{agent['alternateagentaddress1']}{", "+agent['alternateagentaddress2'] if agent['alternateagentaddress2'] else ""}{", "+agent['alternateagentaddress3'] if agent['alternateagentaddress3'] else ""}{", "+agent['alternateagentcity'] if agent['alternateagentcity'] else ""}{", "+agent['alternateagentstate'] if agent['alternateagentstate'] else ""}{", "+agent['alternateagent1zip'] if agent['alternateagent1zip'] else ""}</li>""" if agent['alternateagentaddress1'] else "",
                f"""<ul><li>""" if agent['alternateagent1'] else "",
                f"""<li class="notes"><ul class="other-trade-names">Notes""" if agent['note1'] else "",
                f"""<li class="note1">{agent['note1']}</li>""" if agent['note1'] else "",
                f"""<li class="note2">{agent['note2']}</li>""" if agent['note2'] else "",
                f"""<li class="note3">{agent['note3']}</li>""" if agent['note3'] else "",
                f"""</ul></li>""" if agent['note1'] else "",
                "</ul></div>"
            ])
            comp = re.sub("XXagentXX", agent_info, comp)
        elif len(arr) == 5:
            agents_info = """<div class="registered-agents">"""
            k = arr[3]
            query = re.compile(arr[4], re.IGNORECASE)
            for i in coll_tel.aggregate([{"$match": {"$or" : [{"carriername": query},{"businessname": query},{"holdingcompany": query},{"othertradename1": query},{"othertradename2": query},{"othertradename3": query},{"othertradename4": query},{"dcagent1": query},{"dcagent2": query},{"alternateagent1": query},{"alternateagent2": query}]}},{"$sort": { k: 1 }}]):
                slug = slugify(f"""{i['carriername'] if i['carriername'] else (i['businessname'] if i['businessname'] else "")}-{i['dcagent1'] if i['dcagent1'] else (i['dcagent2'] if i['dcagent2'] else "")}-service-of-process-{i['id']}""")
                agents_info += "".join([
                    f"""<ul id="{i['id']}" class="agent-container">""",
                    f"""<li class="carriername">Carrier:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['carriername'])}">{i['carriername'] if i['carriername'] else ""}</a></li>""",
                    f"""<li class="businessname">Business Name:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['businessname'])}">{i['businessname'] if i['businessname'] else ""}</a></li>""",
                    f"""<li class="holdingcompany">Holding Company:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['holdingcompany'])}">{i['holdingcompany'] if i['holdingcompany'] else ""}</a></li>""",
                    f"""<li class="hqaddress">HQ Address:&nbsp;{i['hqaddress1'] if i['hqaddress1'] else ""}{", "+i['hqaddress2'] if i['hqaddress2'] else ""}{", "+i['hqaddress3'] if i['hqaddress3'] else ""}</li>""",
                    f"""<li class="othertradenames"><ul class="other-trade-names">Other Trade Names""" if i['othertradename1'] else "",
                    f"""<li class="othertradenames1"><a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['othertradename1'])}">{i['othertradename1']}</a></li>""" if i['othertradename1'] else "",
                    f"""<li class="othertradenames2"><a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['othertradename2'])}">{i['othertradename2']}</a></li>""" if i['othertradename2'] else "",
                    f"""<li class="othertradenames3"><a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['othertradename3'])}">{i['othertradename3']}</a></li>""" if i['othertradename3'] else "",
                    f"""<li class="othertradenames4"><a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['othertradename4'])}">{i['othertradename4']}</a></li>""" if i['othertradename4'] else "",
                    f"""</ul></li>""" if i['othertradename1'] else "",
                    f"""<li class="dcagent1">Agent:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['dcagent1'])}">{i['dcagent1']}</a></li>""" if i['dcagent1'] else "",
                    f"""<li class="dcagent2">Agent Two:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['dcagent2'])}">{i['dcagent2']}</a></li>""" if i['dcagent2'] else "",
                    f"""<li class="alternateagent1">Alt Agent:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['alternateagent1'])}">{i['alternateagent1']}</a></li>""" if i['alternateagent1'] else "",
                    f"""<li class="alternateagent2">Alt Agent Two:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['alternateagent2'])}">{i['alternateagent2']}</a></li>""" if i['alternateagent2'] else "",
                    f"""<li class="agent-details"><a href="/telecom-agents/{slug}"><button>Go to Details</button></a></li>""",
                    "</ul>"
                ])
            agents_info += "</div>"
            comp = re.sub("XXagentsXX", agents_info, comp)
            comp = re.sub("XXagentsqueryXX", arr[4].title(), comp)
    corp_links = """<div class="corp-links">"""
    for i in coll_cp.find().sort("name", 1):
        corp_links += f"""<a href="/process-server/{"-".join(i['searchvalue'].split(" "))}-{i['id']}">{i['name']}</a>"""
    corp_links += """</div>"""
    html_sitemap = """<div><ul class="sitemap-links">"""
    for i in s.pages:
        if re.search(r'(^/locations)|(^/registered-agents)|(^/telecom-agents)|(^/process-server)|(/blog/posts/id)|(^/agents-by-state/)|(\.)', i.route) is None:
            if i.route == "/":
                html_sitemap += """<li><a href="/">Home</a></li>"""
            else:
                html_sitemap += f"""<li><a href="{i.route}">{" ".join(i.route.split("/")).title()}</a></li>"""
    html_sitemap += """</ul></div>"""
    corps_in_states = """<div class="state-corps-links">"""
    for i in coll_st.find():
        corps_in_states += f"""<a href="/agents-by-state/{"-".join(i['statename'].split(" "))}">{i['statename'].title()}</a>"""
    corps_in_states += """</div>"""
    comp = re.sub('XXcorpsinstatesXX', corps_in_states, comp)
    comp = re.sub('XXsitemapXX', html_sitemap, comp)
    comp = re.sub('XXcorplinksXX', corp_links, comp)
    comp = re.sub('XXsitenameXX', s.sitename if s.sitename else "", comp)
    comp = re.sub('XXspagetitleXX', spage.title if spage.title else "", comp)
    comp = re.sub('XXrouteXX', r if r else "", comp)
    comp = re.sub('XXspagerouteXX', spage.route if spage.route else "", comp)
    comp = re.sub('XXtemplatenameXX', t.templatename if t.templatename else "", comp)
    comp = re.sub('XXtpagetitleXX', tpage.title if tpage.title else "", comp)
    comp = re.sub('XXtpagerouteXX', tpage.route if tpage.route else "", comp)
    comp = re.sub(r'Ct ', "CT ", comp)
    comp = re.sub(r'C\.t\. ', "C.T. ", comp)
    comp = re.sub(r'Csc', "CSC", comp)
    comp = re.sub(r'C\.s\.c\.', "C.S.C.", comp)
    comp = re.sub(r'Nrai', "NRAI", comp)
    comp = re.sub(r'N\.r\.a\.i\.', "N.R.A.I.", comp)
    comp = re.sub(r'Rasi', "RASI", comp)
    comp = re.sub(r'R\.a\.s\.i\.', "R.A.S.I.", comp)
    comp = re.sub(r'Urs ', "URS ", comp)
    comp = re.sub(r'U\.r\.s\. ', "U.R.S. ", comp)
    comp = re.sub(r'Myllc', "MyLLC", comp)
    comp = re.sub(r'Llc', "LLC", comp)
    comp = re.sub(r'Llc\.', "LLC.", comp)
    comp = re.sub(r'L\.l\.c\.', "L.L.C.", comp)
    comp = re.sub(r'Ltd', "LTD", comp)
    comp = re.sub(r'Ltd\.', "LTD.", comp)
    comp = re.sub(r'L\.t\.d\.', "L.T.D.", comp)
    comp = re.sub(r'New york', "New York", comp)
    comp = re.sub(r'New jersey', "New Jersey", comp)
    comp = re.sub(r'New mexico', "New Mexico", comp)
    comp = re.sub(r'North carolina', "North Carolina", comp)
    comp = re.sub(r'South carolina', "South Carolina", comp)
    comp = re.sub(r'North dakota', "North Dakota", comp)
    comp = re.sub(r'South dakota', "South Dakota", comp)
    comp = re.sub(r'West virginia', "West Virginia", comp)
    comp = re.sub(r'Dc', "DC", comp)
    comp = re.sub(r'D\.c\. ', "D.C.", comp)
    comp = re.sub(r'District of columbia', "District of Columbia", comp)
    comp = replace_shortcodes(s, t, comp)
    comp = replace_shortcodes(s, t, comp)
    return comp



def replace_shortcodes(site, template, string_content):
    compiled = string_content
    for i in site.shortcodes:
        reg = re.compile(f"""XX{i.name}XX""")
        compiled = re.sub(reg, i.value, compiled)
    for i in template.shortcodes:
        reg = re.compile(f"""XX{i.name}XX""")
        compiled = re.sub(reg, i.value, compiled)
    return compiled


def render_robots(s, t):
    robots = ""
    robots += " " 
    return robots


def render_xml_sitemap(s, t, rt):
    sitemap_urls = []
    for i in s.pages:
        if re.search(r'^/locations/', i.route) is not None:
            if len(i.route.split("/")) == 3:
                sitemap_urls.append("".join(list(map(lambda n: f"""<url><loc>https://www.{s.sitename}.com/locations/{n['statename']}</loc></url>""", coll_st.find()))))
            elif len(i.route.split("/")) == 5:
                sitemap_urls.append("".join(list(map(lambda n: f"""<url><loc>https://www.{s.sitename}.com/locations/{n['statename']}/{n['countyname']}-{n['countyid']}/{n['cityname']}-{n['id']}</loc></url>""", coll_ci.find()))))
        elif re.search(r'^/blog/', i.route) is not None:
            if len(i.route.split("/")) == 3:
                sitemap_urls.append(f"""<url><loc>https://www.{s.sitename}.com{i.route}</loc></url>""")
            elif len(i.route.split("/")) == 4:
                sitemap_urls.append("".join(list(map(lambda n: f"""<url><loc>https://www.{s.sitename}.com/blog/posts/{n['bloguri'] if n['bloguri'] else ""}-{n['id']}</loc></url>""", coll_bl.find({'blogcategory': s.blogcategory})))))
        elif re.search(r'^/registered-agents/', i.route) is not None:
            if re.search(r'^/registered-agents/search', i.route) is not None:
                import urllib.parse
                for n in ["company", "agency", "state", "city"]:
                    sitemap_urls.append("".join(list(map(lambda k: "".join([f"""<url><loc>https://www.{s.sitename}.com""", urllib.parse.quote(f"""/registered-agents/search/{n}/{k.lower()}"""), "</loc></url>"]), coll_ra.find().distinct(n)))))
            else:
                sitemap_urls.append("".join(list(map(lambda n: f"""<url><loc>https://www.{s.sitename}.com/registered-agents/service-of-process-{n['id']}</loc></url>""", coll_ra.find()))))
        elif re.search(r'^/telecom-agents/', i.route) is not None:
            if re.search(r'^/telecom-agents/search', i.route) is not None:
                import urllib.parse
                for n in ['carriername', 'businessname', 'holdingcompany', 'othertradename1', 'othertradename2', 'othertradename3', 'othertradename4', 'dcagent1', 'dcagent2', 'dcagentcity', 'dcagentstate']:
                    sitemap_urls.append("".join(list(map(lambda k: "".join([f"""<url><loc>https://www.{s.sitename}.com""", urllib.parse.quote(f"""/telecom-agents/search/{n}/{k.lower()}"""), "</loc></url>"]), coll_tel.find().distinct(n)))))
            else:
                sitemap_urls.append("".join(list(map(lambda n: f"""<url><loc>https://www.{s.sitename}.com/telecom-agents/service-of-process-{n['id']}</loc></url>""", coll_tel.find()))))
        elif re.search(r'^/process-server/', i.route) is not None:
            if re.search(r'^/process-server/id/state/city', i.route) is not None:
                # nested map lambda functions to get all three layers of permutated dynamic url routes simultaneously
                sitemap_urls.append("".join(list(map(lambda n: "".join([f"""<url><loc>https://www.{s.sitename}.com/process-server/{"-".join(n['name'].split(" ")).lower()}-{n['id']}</loc></url>""", "".join(list(map(lambda k: "".join([f"""<url><loc>https://www.{s.sitename}.com/process-server/{"-".join(n['name'].split(" ")).lower()}-{n['id']}/{"-".join(k.split(" ")).lower()}</loc></url>""", "".join(list(map(lambda m: f"""<url><loc>https://www.{s.sitename}.com/process-server/{"-".join(n['name'].split(" ")).lower()}-{n['id']}/{"-".join(k.split(" ")).lower()}/{"-".join(m.split(" ")).lower()}</loc></url>""", coll_ra.find({'state': k}).distinct('city'))))]), coll_ra.find().distinct("state"))))]), coll_cp.find()))))
        else:
            if re.search(r'\.[a-z]{2,4}$', i.route) is None:
                sitemap_urls.append(f"""<url><loc>https://www.{s.sitename}.com{i.route}</loc></url>""")
    sitemap = "".join(["""<?xml version="1.0" encoding="utf-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">""", "".join(sitemap_urls), """</urlset>"""])
    return sitemap




#for m in lev_and_cos_search()[0:10]:
    #pp.pprint(coll_ra.find_one({'id': int(m[0])}))


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

