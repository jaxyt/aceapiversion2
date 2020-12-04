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
from urllib.parse import quote, unquote


import linecache
import sys

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print(f"""EXCEPTION IN ({filename}, LINE {lineno} "{line.strip()}"): {exc_obj}""")


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
coll_telco = db.registeredagents_telecomcorps
coll_tel = db.registeredagents_telecom

def registered_agent_search(k, q):
    res = []
    query = re.compile(q, re.IGNORECASE)
    for i in coll_ra.find({k: query}):
        res.append(i)
    return res

def no_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def compiler_v3(s, t, r, arr):
    try:
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
            elif len(arr) == 4 or (len(arr) == 5 and arr[4] == ""):
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
        meta_data = ""
        if spage:
            if spage.pagemetas:
                cont = no_html_tags(spage.content)
                cont = re.sub(r'"', '', cont)
                cont = re.sub(r"'", "", cont)
                cont = re.sub(r"\n", " ", cont)
                cont = re.sub(r"\s{2,}", " ", cont)
                read_time = round(len(cont.split(" "))/250)
                meta_data = "".join([
                    f"""<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">""",
                    f"""<link rel="canonical" href="https://www.XXsitenameXX.comXXrouteXX">""",
                    f"""<meta property="og:locale" content="en_US">""",
                    f"""<meta property="og:type" content="website">""",
                    f"""<meta property="og:title" content="{spage.title if spage.title else tpage.title if tpage.title else ""}{' - ' + s.sitedisplayname if s.sitedisplayname else 'XXsitenameXX'}">""",
                    f"""<meta property="og:description" content="{re.search(r'(?<=<meta name="description" content=")(.)+(?="/?>)', spage.pagemetas).group() }">""" if re.search(r'(?<=<meta name="description" content=")(.)+(?="/?>)', spage.pagemetas) else "",
                    f"""<meta property="og:url" content="https://www.XXsitenameXX.comXXrouteXX">""",
                    f"""<meta property="og:site_name" content="{s.sitedisplayname if s.sitedisplayname else 'XXsitenameXX'}">""",
                    f"""<meta property="article:publisher" content="{s.facebookurl}">""" if s.facebookurl else '',
                    f"""<meta name="twitter:card" content="summary_large_image">""",
                    f"""<meta name="twitter:creator" content="@{s.twitterusername}">""" if s.twitterusername else '',
                    f"""<meta name="twitter:site" content="@{s.twitterusername}">""" if s.twitterusername else '',
                    f"""<meta name="twitter:label1" content="Written by">""",
                    f"""<meta name="twitter:data1" content="GoshGo">""",
                    f"""<meta name="twitter:label2" content="Est. reading time">""",
                    f"""<meta name="twitter:data2" content="{read_time} minutes">""" if read_time else '',
                    f"""<script type="application/ld+json">""",
                    """ {""",
                    f""" "@context":"https://schema.org", """,
                    f""" "@graph": """,
                    """ [{""",
                    f""" "@type":"Organization", """,
                    f""" "@id":"https://www.XXsitenameXX.com/#organization", """,
                    f""" "name":"{s.organizationname if s.organizationname else ''}", """,
                    f""" "url":"https://www.XXsitenameXX.com/", """,
                    f""" "sameAs":[ "{s.facebookurl if s.facebookurl else ''}", "{s.linkedinurl if s.linkedinurl else ''}", "https://twitter.com/{s.twitterusername if s.twitterusername else ''}" """+""" ],""" if s.twitterusername or s.linkedinurl or s.facebookurl else '',
                    f""" "logo": """,
                    """ {""",
                    f""" "@type":"ImageObject",""",
                    f""" "@id":"https://www.XXsitenameXX.com/#logo",""",
                    f""" "inLanguage":"en-US",""",
                    f""" "url":"https://www.XXsitenameXX.com{s.logoroute}",""" if s.logoroute else '',
                    f""" "width":{s.logowidth},""" if s.logowidth else '',
                    f""" "height":{s.logoheight},""" if s.logoheight else '',
                    f""" "caption":"{s.organizationname}" """ if s.organizationname else '',
                    """ },""",
                    f""" "image":""",
                    """ {""",
                    f""" "@id":"https://www.XXsitenameXX.com/#logo" """,
                    """ } }, {""",
                    f""" "@type":"WebSite",""",
                    f""" "@id":"https://www.XXsitenameXX.com/#website",""",
                    f""" "url":"https://www.XXsitenameXX.com/",""",
                    f""" "name":"{s.sitedisplayname if s.sitedisplayname else 'XXsitenameXX'}",""",
                    f""" "description":"{s.sitedescription}",""" if s.sitedescription else '',
                    f""" "publisher":""",
                    """ {""",
                    f""" "@id":"https://www.XXsitenameXX.com/#organization" """,
                    """ }, "potentialAction": [{"""+f""" "@type":"SearchAction", "target":"https://www.XXsitenameXX.com{s.searchroute}"""+"""{search_term_string}", "query-input":"required name=search_term_string" }],""" if s.searchroute else '',
                    f""" "inLanguage":"en-US" """,
                    """ }, {""",
                    f""" "@type":"WebPage",""",
                    f""" "@id":"https://www.XXsitenameXX.comXXrouteXX#webpage",""",
                    f""" "url":"https://www.XXsitenameXX.comXXrouteXX",""",
                    f""" "name":"{spage.title if spage.title else tpage.title if tpage.title else ""}{' - ' + s.sitedisplayname if s.sitedisplayname else 'XXsitenameXX'}",""",
                    f""" "isPartOf":""",
                    """ {""",
                    f""" "@id":"https://www.XXsitenameXX.com/#website" """,
                    """ },""",
                    f""" "about":""",
                    """ {""",
                    f""" "@id":"https://www.XXsitenameXX.com/#organization" """,
                    """ },""",
                    f""" "description":"{re.search(r'(?<=<meta name="description" content=")(.)+(?="/?>)', spage.pagemetas).group()}","""  if re.search(r'(?<=<meta name="description" content=")(.)+(?="/?>)', spage.pagemetas) else "",
                    """ "inLanguage":"en-US","potentialAction":[{"@type":"ReadAction","target":[ "https://www.XXsitenameXX.comXXrouteXX"] }] }] }""",
                    f"""</script>""",
                ])
        comp = "\n".join([ 
            "<!DOCTYPE html>",
            """<html dir="ltr" lang="en">""",
            "<head>",
            f"""{s.sitemetas if s.sitemetas else t.sitemetas if t.sitemetas else ""}""",
            f"""{spage.pagemetas if spage.pagemetas else tpage.pagemetas if tpage.pagemetas else ""}""",
            f"""{s.sitelinks if s.sitelinks else t.sitelinks if t.sitelinks else ""}""",
            f"""{spage.pagelinks if spage.pagelinks else tpage.pagelinks if tpage.pagelinks else ""}""",
            f"""<title>{spage.title if spage.title else tpage.title if tpage.title else ""}</title>""",
            meta_data,
            f"""{spage.pagestyle if spage.pagestyle else s.sitestyle if s.sitestyle else tpage.pagestyle if tpage.pagestyle else t.sitestyle if t.sitestyle else ""}""",
            "</head>",
            "<body>",
            f"""{spage.pageheader if spage.pageheader else s.siteheader if s.siteheader else tpage.pageheader if tpage.pageheader else t.siteheader if t.siteheader else ""}""",
            f"""{spage.content if spage.content else tpage.content if tpage.content else ""}""",
            f"""{spage.pagefooter if spage.pagefooter else s.sitefooter if s.sitefooter else tpage.pagefooter if tpage.pagefooter else t.sitefooter if t.sitefooter else ""}""",
            f"""{s.sitescripts if s.sitescripts else t.sitescripts if t.sitescripts else ""}""",
            f"""{spage.pagescripts if spage.pagescripts else tpage.pagescripts if tpage.pagescripts else ""}""",
            "</body>",
            "</html>",
        ])
        
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
                    f"""<li class="address">Address:&nbsp;{agent['address'].title()}</li>""" if agent['address'] else "",
                    "</ul></div>"
                ])
                comp = re.sub("XXagentXX", agent_info, comp)
                comp = re.sub("XXagentagencyXX", f"""{agent['agency'].title() if agent['agency'] else ""}""", comp)
                comp = re.sub("XXagentcompanyXX", f"""{agent['company'].title() if agent['company'] else ""}""", comp)
                comp = re.sub("XXagentstateXX", f"""{agent['state'].title() if agent['state'] else ""}""", comp)
                comp = re.sub("XXagentcityXX", f"""{agent['city'].title() if agent['city'] else ""}""", comp)
                comp = re.sub("XXagentaddressXX", f"""{agent['address'].title() if agent['address'] else ""}""", comp)
                comp = re.sub("XXcorpXX", f"""{agent['company'].title() if agent['company'] else agent['agency'].title() if agent['agency'] else ""}""", comp)
                if agent['state']:
                    if agent['state'] != 'DC':
                        rege = re.compile(agent['state'], re.IGNORECASE)
                        agent_state = coll_st.find_one({"statename": rege})
                        state_acronym = agent_state['stateacronym']
                        comp = re.sub(r"XXstateacronymXX", state_acronym, comp)
                    else:
                        comp = re.sub(r"XXstateacronymXX", 'DC', comp)
                else:
                    comp = re.sub(r"XXstateacronymXX", "", comp)
            elif len(arr) == 5:
                from urllib.parse import unquote
                #from .tests2 import lev_and_cos_search
                agents_info = """
<div class="table-responsive">
    <table id="default_order" class="table table-striped table-bordered display" style="width:100%">
        <thead>
            <tr>
                <th>Details</th>
                <th>Registered Agent</th>
                <th>Address</th>
            </tr>
        </thead>
        <tbody>
                """
                k = arr[3]
                q = unquote(arr[4])
                q = re.sub(r'[^\w\s]','',q)
                q = re.sub(r'\s{2,}','',q)
                q = q.strip(" ")
                #search_results = lev_and_cos_search(q)
                search_results = coll_ra.find({"$text":{"$search":q}},{"score":{"$meta":"textScore"}}).sort([("score",{"$meta":"textScore"})])
                for m in search_results:
                    #current_agent = coll_ra.find_one({'id': int(m[0])})
                    slug = slugify(f"""{m['company'] if m['company'] else (m['agency'] if m['agency'] else "")}-service-of-process-{m['id']}""")
                    agents_info += f"""
            <tr>
                <td><a href="/registered-agents/{slug}"><button type="button" class="btn waves-effect waves-light btn-info">Info</button></a></td>
                <td>{m['company'].title() if m['company'] else m['agency'].title()}</td>
                <td><a href="/registered-agents/{slug}">{m['address'].title() if m['address'] else ""}</a></td>
            </tr>
                    """
                    #  agents_info += "".join([
                    #      f"""<tr id="{m['id']}">""",
                    #      f"""<td><a href="/registered-agents/{slug}"><button type="button" class="btn waves-effect waves-light btn-info">Info</button></a></td>""",
                    #      f"""<td>{m['company'].title() if m['company'] else m['agency'].title()}</td>""",
                    #      f"""<td class="address"><a href="/registered-agents/{slug}">{m['address'].title()}</a></td>""" if m['address'] else "<td></td>",
                    #      "</tr>"
                    #  ])
                agents_info += """
        </tbody>
    </table>
</div>
                """
                comp = re.sub("XXagentsXX", agents_info, comp)
                comp = re.sub("XXagentsqueryXX", arr[4].title(), comp)
        elif arr[1] == "process-server":
            if len(arr) == 3:
                agents_info = """
<div class="table-responsive">
    <table id="default_order" class="table table-striped table-bordered display" style="width:100%">
        <thead>
            <tr>
                <th>Details</th>
                <th>Registered Agent</th>
                <th>Address</th>
            </tr>
        </thead>
        <tbody>
                """
                corp = coll_cp.find_one({'id': int(arr[2].split("-")[-1])})
                k = corp['searchkey']
                q = corp['searchvalue']
                # <a href="/registered-agents/search/city/{i['city']}, {i['state']}">
                query = re.compile(q, re.IGNORECASE)
                for i in coll_ra.find({k: query}):
                    slug = slugify(f"""{i['company'] if i['company'] else (i['agency'] if i['agency'] else "")}-service-of-process-{i['id']}""")
                    agents_info += f"""
            <tr>
                <td><a href="/registered-agents/{slug}"><button type="button" class="btn waves-effect waves-light btn-info">Info</button></a></td>
                <td>{i['company'].title() if i['company'] else i['agency'].title()}</td>
                <td><a href="/registered-agents/{slug}">{i['address'].title() if i['address'] else ""}</a></td>
            </tr>
                    """
                agents_info += """
        </tbody>
    </table>
</div>
                """
                comp = re.sub('XXagentsXX', agents_info, comp)
                comp = re.sub('XXcorpXX', corp['name'], comp)
                corps_in_states = """<div class="process-server-corp-state-links">"""
                for i in coll_st.find():
                    corps_in_states += f"""<a href="{"/".join(arr)}/{"-".join(i['statename'].split(" "))}">{i['statename'].title()}</a>"""
                corps_in_states += """</div>"""
                comp = re.sub('XXcorpsinstatesXX', corps_in_states, comp)
            elif len(arr) == 4 or (len(arr) == 5 and arr[4] == ""):
                agents_info = """
<div class="table-responsive">
    <table id="default_order" class="table table-striped table-bordered display" style="width:100%">
        <thead>
            <tr>
                <th>Details</th>
                <th>Registered Agent</th>
                <th>Address</th>
            </tr>
        </thead>
        <tbody>
                """
                corp = coll_cp.find_one({'id': int(arr[2].split("-")[-1])})
                st = " ".join(arr[3].split("-"))
                st = re.sub('Washington District of Columbia', 'DC', st)
                k = corp['searchkey']
                q = corp['searchvalue']
                query = re.compile(q, re.IGNORECASE)
                state_query = re.compile(st.lower(), re.IGNORECASE)
                for i in coll_ra.find({k: query, 'state': state_query}):
                    slug = slugify(f"""{i['company'] if i['company'] else (i['agency'] if i['agency'] else "")}-service-of-process-{i['id']}""")
                    agents_info += f"""
            <tr>
                <td><a href="/registered-agents/{slug}"><button type="button" class="btn waves-effect waves-light btn-info">Info</button></a></td>
                <td>{i['company'].title() if i['company'] else i['agency'].title()}</td>
                <td><a href="/registered-agents/{slug}">{i['address'].title() if i['address'] else ""}</a></td>
            </tr>
                    """
                agents_info += """
        </tbody>
    </table>
</div>
                """
                comp = re.sub('XXagentsXX', agents_info, comp)
                comp = re.sub('XXcorpXX', corp['name'], comp)
                comp = re.sub('XXstatequeryXX', st.title(), comp)
                corps_in_cities = """<div class="process-server-corps-city-links">"""
                for i in coll_ra.find({k: query, 'state': state_query}).distinct('city'):
                    corps_in_cities += f"""<a href="{("/".join(arr))}/{"-".join(i.lower().split(" "))}">{i.title()}</a>""" if i else ""
                corps_in_cities += """</div>"""
                corps_in_cities = re.sub(r'(?<!https:)//', "/", corps_in_cities)
                comp = re.sub('XXcitycorpsXX', corps_in_cities, comp)
            elif len(arr) == 5:
                agents_info = """
<div class="table-responsive">
    <table id="default_order" class="table table-striped table-bordered display" style="width:100%">
        <thead>
            <tr>
                <th>Details</th>
                <th>Registered Agent</th>
                <th>Address</th>
            </tr>
        </thead>
        <tbody>
                """
                corp = coll_cp.find_one({'id': int(arr[2].split("-")[-1])})
                st = " ".join(arr[3].split("-"))
                st = re.sub('Washington District of Columbia', 'DC', st)
                cit = " ".join(arr[4].split("-"))
                k = corp['searchkey']
                q = corp['searchvalue']
                query = re.compile(q, re.IGNORECASE)
                state_query = re.compile(st.lower(), re.IGNORECASE)
                city_query = re.compile(cit.lower(), re.IGNORECASE)
                for i in coll_ra.find({k: query, 'state': state_query, 'city': city_query}):
                    slug = slugify(f"""{i['company'] if i['company'] else (i['agency'] if i['agency'] else "")}-service-of-process-{i['id']}""")
                    agents_info += f"""
            <tr>
                <td><a href="/registered-agents/{slug}"><button type="button" class="btn waves-effect waves-light btn-info">Info</button></a></td>
                <td>{i['company'].title() if i['company'] else i['agency'].title()}</td>
                <td><a href="/registered-agents/{slug}">{i['address'].title() if i['address'] else ""}</a></td>
            </tr>
                    """
                agents_info += """
        </tbody>
    </table>
</div>
                """
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
                agents_info = """
<div class="table-responsive">
    <table id="default_order" class="table table-striped table-bordered display" style="width:100%">
        <thead>
            <tr>
                <th>Details</th>
                <th>Registered Agent</th>
                <th>Address</th>
            </tr>
        </thead>
        <tbody>
                """
                st = " ".join(arr[2].split("-")) if re.match('washington-district-of-columbia', arr[2]) is None else "dc"
                state_query = re.compile(st.lower(), re.IGNORECASE)
                for i in coll_ra.find({'state': state_query}):
                    slug = slugify(f"""{i['company'] if i['company'] else (i['agency'] if i['agency'] else "")}-service-of-process-{i['id']}""")
                    agents_info += f"""
            <tr>
                <td><a href="/registered-agents/{slug}"><button type="button" class="btn waves-effect waves-light btn-info">Info</button></a></td>
                <td>{i['company'].title() if i['company'] else i['agency'].title()}</td>
                <td><a href="/registered-agents/{slug}">{i['address'].title() if i['address'] else ""}</a></td>
            </tr>
                    """
                agents_info += """
        </tbody>
    </table>
</div>
                """
                comp = re.sub('XXagentsXX', agents_info, comp)
                comp = re.sub('XXstatequeryXX', st.title(), comp)
                corps_in_cities = """<div class="corps-in-city-links">"""
                for i in coll_ra.find({'state': state_query}).distinct('city'):
                    corps_in_cities += f"""<a href="{"/".join(arr)}/{"-".join(i.lower().split(" "))}">{i.title()}</a>""" if i else ""
                corps_in_cities += """</div>"""
                comp = re.sub('XXcitycorpsXX', corps_in_cities, comp)
            elif len(arr) == 4:
                agents_info = """
<div class="table-responsive">
    <table id="default_order" class="table table-striped table-bordered display" style="width:100%">
        <thead>
            <tr>
                <th>Details</th>
                <th>Registered Agent</th>
                <th>Address</th>
            </tr>
        </thead>
        <tbody>
                """
                st = " ".join(arr[2].split("-"))
                cit = " ".join(arr[3].split("-"))
                state_query = re.compile(st.lower(), re.IGNORECASE)
                city_query = re.compile(cit.lower(), re.IGNORECASE)
                for i in coll_ra.find({'state': state_query, 'city': city_query}):
                    slug = slugify(f"""{i['company'] if i['company'] else (i['agency'] if i['agency'] else "")}-service-of-process-{i['id']}""")
                    agents_info += f"""
            <tr>
                <td><a href="/registered-agents/{slug}"><button type="button" class="btn waves-effect waves-light btn-info">Info</button></a></td>
                <td>{i['company'].title() if i['company'] else i['agency'].title()}</td>
                <td><a href="/registered-agents/{slug}">{i['address'].title() if i['address'] else ""}</a></td>
            </tr>
                    """
                agents_info += """
        </tbody>
    </table>
</div>
                """
                comp = re.sub('XXagentsXX', agents_info, comp)
                comp = re.sub('XXstatequeryXX', st.title(), comp)
                comp = re.sub('XXcityqueryXX', cit.title(), comp)
        elif arr[1] == "telecom-agents":
            
            if len(arr) == 3:
                print(arr[2])
                agent = coll_tel.find_one({'id': int(arr[2].split("-")[-1])})
                agent_info = "".join([
                    f"""<div class="registered-agent"><ul id="{agent['id']}" class="agent-container">""",
                    f"""<li class="t-agent">Registered Agent(s): {agent['dcagent1']}</li>""",
                    f"""<li class="carriername">Legal Name of Carrier: {agent['carriername']}</li>""",
                    f"""<li class="businessname">Business Name: {agent['businessname']}</li>""" if agent['businessname'] else "",
                    f"""<li class="holdingcompany">Holding Company: {agent['holdingcompany']}</li>""" if agent['holdingcompany'] else "",
                    f"""<li class="othertradenames">Other Trade Names: {agent['othertradename1']}</li>""" if agent['othertradename1'] else "",
                    f"""<li class="dcagentaddress">Address: {agent['dcagentaddress1']}</li>""",
                    "</ul></div>"
                ])
                comp = re.sub("XXagentXX", agent_info, comp)
            elif len(arr) == 5:
                from urllib.parse import unquote
                agents_info = """
<div class="table-responsive">
    <table id="default_order" class="table table-striped table-bordered display" style="width:100%">
        <thead>
            <tr>
                <th>Details</th>
                <th>Registered Agent</th>
                <th>Agent Address</th>
                <th>Carrier</th>
            </tr>
        </thead>
        <tbody>
                """
                q = unquote(arr[4])
                q = re.sub(r'[^\w\s]','',q)
                q = re.sub(r'\s{2,}','',q)
                q = q.strip(" ")
                search_results = coll_tel.find({"$text":{"$search":q}},{"score":{"$meta":"textScore"}}).sort([("score",{"$meta":"textScore"})]) if arr[4] != "" else coll_tel.find()
                for m in search_results:
                    slug = slugify(f"""{m['carriername']}-{m['dcagent1']}-service-of-process-{m['id']}""")
                    agents_info += f"""
            <tr id="{m['id']}">
                <td><a href="/telecom-agents/{slug}"><button type="button" class="btn waves-effect waves-light btn-info">Info</button></a></td>
                <td>{m['dcagent1']}</td>
                <td><a href="/telecom-agents/{slug}">{m['dcagentaddress1']}</a></td>
                <td>{m['carriername']}</td>
            </tr>
                    """
                agents_info += """
        </tbody>
    </table>
</div>
                """
                comp = re.sub("XXagentsXX", agents_info, comp)
                comp = re.sub("XXagentsqueryXX", arr[4].title(), comp)
        corp_links = """<div class="corp-links">"""
        for i in coll_cp.find().sort("name", 1):
            corp_links += f"""<a class="btn btn-info" role="button" href="/process-server/{"-".join(i['searchvalue'].split(" "))}-{i['id']}">{i['name']}</a>"""
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
        if re.match(r'-9$', r):
            print(comp)
        return comp
    except Exception as e:
        PrintException()
        print(e)
        raise Exception(e)



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
                
                for n in ["company", "agency", "state", "city"]:
                    sitemap_urls.append("".join(list(map(lambda k: "".join([f"""<url><loc>https://www.{s.sitename}.com""", quote(f"""/registered-agents/search/{n}/{k.lower()}"""), "</loc></url>"]), coll_ra.find().distinct(n)))))
            else:
                sitemap_urls.append("".join(list(map(lambda n: f"""<url><loc>https://www.{s.sitename}.com/registered-agents/service-of-process-{n['id']}</loc></url>""", coll_ra.find()))))
        elif re.search(r'^/telecom-agents/', i.route) is not None:
            if re.search(r'^/telecom-agents/search', i.route) is not None:
                
                for n in ['carriername', 'businessname', 'holdingcompany', 'othertradename1', 'othertradename2', 'othertradename3', 'othertradename4', 'dcagent1', 'dcagent2', 'dcagentcity', 'dcagentstate']:
                    sitemap_urls.append("".join(list(map(lambda k: "".join([f"""<url><loc>https://www.{s.sitename}.com""", quote(f"""/telecom-agents/search/{n}/{k.lower()}"""), "</loc></url>"]), coll_tel.find().distinct(n)))))
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


desired_states = [
    'new york',
    'arizona',
    'california',
    'arkansas',
    'nevada',
    'florida',
    'colorado',
    'michigan',
    'texas',
    'pennsylvania',
    'oregon',
    'north carolina',
    'new jersey',
]
st_combined = "(" + ")|(".join(desired_states) + ")"
st_rx = re.compile(st_combined, re.IGNORECASE)


def myFunc(e):
        return len(e)


def process_server_sitemap(s, rt, m):
    """
    docstring
    """
    locs = []
    for i in coll_cp.find({}, {'_id': 0}):
        locs.append(f"https://www.{s['sitename']}.com{m}{slugify(i['searchvalue'])}-{i['id']}")
        for n in coll_ci.find({}, {'_id': 0}):
            if re.search(st_rx, n['statename']):
                # locs.append(f"https://www.{s['sitename']}.com{m}{slugify(i['searchvalue'])}-{i['id']}/{slugify(n['statename'])}")
                locs.append(f"https://www.{s['sitename']}.com{m}{slugify(i['searchvalue'])}-{i['id']}/{slugify(n['statename'])}/{slugify(n['cityname'])}")
    return list(set(locs)) if locs != [] else None


def registered_agents_sitemap(s, rt, m):
    """
    docstring
    """
    locs = []
    for i in coll_ra.find({}, {'_id': 0}):
        locs.append(f"https://www.{s['sitename']}.com{m}{slugify(i['company'] if i['company'] else i['agency'])}-registered-agent-service-of-process-{i['id']}")
        locs.append(f"https://www.{s['sitename']}.com{m}search/registered-agent-process-servers/"+quote(f"{i['company'] if i['company'] else i['agency']}".capitalize()))
        if i['state']:
            locs.append(f"https://www.{s['sitename']}.com{m}search/registered-agent-process-servers/"+quote(f"{i['company'] if i['company'] else i['agency']}".capitalize()+", "+f"{i['state']}".capitalize()))
            if i['city']:
                locs.append(f"https://www.{s['sitename']}.com{m}search/registered-agent-process-servers/"+quote(f"{i['state']}".capitalize()+", "+f"{i['city']}".capitalize()))
    return list(set(locs)) if locs != [] else None


def telecom_agents_sitemap(s, rt, m):
    """
    docstring
    """
    locs = []
    for i in coll_tel.find({}, {'_id': 0}):
        locs.append(f"https://www.{s['sitename']}.com{m}{slugify(i['carriername'])}-{slugify(i['dcagent1'])}-registered-agent-service-of-process-washington-dc-{i['id']}")
        locs.append(f"https://www.{s['sitename']}.com{m}washington-dc-telecom-registered-agent-process-servers/"+quote(f"{i['carriername']}".capitalize()))
        locs.append(f"https://www.{s['sitename']}.com{m}washington-dc-telecom-registered-agent-process-servers/"+quote(f"{i['dcagent1']}".capitalize()))
    return list(set(locs))


def agents_by_state_sitemap(s, rt, m):
    """
    docstring
    """
    locs = []
    for i in coll_ra.find({}, {'_id': 0}):
        if i['state']:
            locs.append(f"https://www.{s['sitename']}.com{m}{slugify(i['state'])}")
            if i['city']:
                locs.append(f"https://www.{s['sitename']}.com{m}{slugify(i['state'])}/{slugify(i['city'])}")
    return list(set(locs))


def locations_sitemap(s, rt, m):
    """
    docstring
    """
    locs = []
    for i in coll_ci.find({}, {'_id': 0}):
        locs.append(f"https://www.{s['sitename']}.com{m}{slugify(i['statename'])}")
        locs.append(f"https://www.{s['sitename']}.com{m}{slugify(i['statename'])}/{slugify(i['countyname'])}-{i['countyid']}/{slugify(i['cityname'])}-{i['id']}")
    return list(set(locs))


def blog_posts_sitemap(s, rt, m):
    """
    docstring
    """
    res = list(map(lambda x: f"https://www.{s['sitename']}.com{m}{slugify(x['title'])}-{x['id']}", coll_bl.find({'blogcategory': s['blogcategory']}, {'_id': 0})))
    return res



def render_xml_sitemap2(s, rt):
    dynamics = [
        '^/registered-agents/',
        '^/blog/posts/',
        '^/process-server/',
        '^/agents-by-state/',
        '^/telecom-agents/',
        '^/locations/',   
    ]
    params = [
        '/id',
        '/key',
        '/value',
        '/state',
        '/county',
        '/city',
    ]
    excluded_extensions = [
        '\.js$',
        '\.css$',
        '\.py$',
        '\.xml$',
        '\.json$',
        '\.scss$',
        '\.pdf$',
        '^\.htaccess$',
        '\.txt$',
        '\.java$',
        '\.svg$',
    ]
    dy_combined = "(" + ")|(".join(dynamics) + ")"
    pa_combined = "(" + ")|(".join(params) + ")"
    ex_combined = "(" + ")|(".join(excluded_extensions) + ")"
    url_count = 0
    sitemap_num = int(re.search(r'\d+', rt).group()) if re.search(r'\d+', rt) else 1
    sitemap_map = {
        'registeredagents': [],
        'blogposts': [],
        'processserver': [],
        'agentsbystate': [],
        'telecomagents': [],
        'locations': [],
    }
    sitemap_urls = []
    sitemap_index = []
    sitemaps_needed = 1
    sitemap_open = """<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"> \n\t<url>\n\t\t<loc>"""
    sitemap_close = """</loc>\n\t</url>\n</urlset>"""
    max_urls = 100
    sitemap_size = 0
    sitemap = ''
    pages = s['pages']
    # print(len(pages))
    for idx, val in enumerate(pages):
        # print(f"""{idx}: {val['route']}""")
        if re.search(ex_combined, val['route']):
            pass
        else:
            if not re.match(dy_combined, val['route']):
                sitemap_urls.append(val['route'])
                url_count += 1
            else:
                dy_route = re.match(dy_combined, val['route']).group()
                if dy_route == '/registered-agents/':
                    if re.search('/id', val['route']):
                        sitemap_map['registeredagents'] = registered_agents_sitemap(s, val['route'], dy_route)
                elif dy_route == '/blog/posts/':
                    if re.search('/id', val['route']):
                        sitemap_map['blogposts'] = blog_posts_sitemap(s, val['route'], dy_route)
                elif dy_route == '/process-server/':
                    if re.search('/city', val['route']):
                        sitemap_map['processserver'] = process_server_sitemap(s, val['route'], dy_route)
                elif dy_route == '/agents-by-state/':
                    if re.search('/city', val['route']):
                        sitemap_map['agentsbystate'] = agents_by_state_sitemap(s, val['route'], dy_route)
                elif dy_route == '/telecom-agents/':
                    if re.search('/id', val['route']):
                        sitemap_map['telecomagents'] = telecom_agents_sitemap(s, val['route'], dy_route)
                elif dy_route == '/locations/':
                    if re.search('/city', val['route']):
                        sitemap_map['locations'] = locations_sitemap(s, val['route'], dy_route)
    for i in ['telecomagents', 'registeredagents', 'agentsbystate', 'processserver', 'locations']:
        for n in sitemap_map[i]:
            sitemap_urls.append(n)
    sitemap_urls = list(set(sitemap_urls))
    sitemap_urls.sort(key=myFunc, reverse=True)
    # print(sitemap_urls)
    url_count = len(sitemap_urls)
    sitemaps_needed = url_count//max_urls
    # print(f"{sitemaps_needed} sitemap(s) needed.")
    if sitemaps_needed == 1:
        sitemap_urls.sort(key=myFunc, reverse=True)
        sitemap = f"{sitemap_open}"+"</loc>\n\t</url>\n\t<url>\n\t\t<loc>".join(sitemap_urls)+f"{sitemap_close}"
        return sitemap
    else:
        for i in range(sitemaps_needed):
            nmap = []
            for n in range(i*max_urls, (i+1)*max_urls):
                if n < url_count:
                    nmap.append(sitemap_urls[n])
                else:
                    break
            sitemap_index.append(nmap)
        #print(sitemap_num.group())
        sitemap_index[sitemap_num].sort(key=myFunc, reverse=True)
        sitemap = f"{sitemap_open}"+"</loc>\n\t</url>\n\t<url>\n\t\t<loc>".join(sitemap_index[sitemap_num])+f"{sitemap_close}"
        # print(f"{len(sitemap_index[sitemap_num])} urls")
        # print(f"Total Filesize: {sys.getsizeof(sitemap)*(1/1000000)}MBs")
        # print(f"{sitemap[0:1000]}")
        # print("...")
        # print(f"{sitemap[-1000:]}")
        # f_name = os.path.join(os.path.dirname(__file__), f"{rt}".split("/")[-1])
        # f = open(f_name, 'w')
        # f.write(sitemap)
        # f.close()
        # os.path.abspath(f_name)
        return sitemap


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


# coll_ra.find({"$text":{"$search":"dothan"}},{"score":{"$meta":"textScore"}}).sort([("score",{"$meta":"textScore"})])
def do_mongo_query(collection):
    res = False
    try:
        # json.dumps(list(map(add_to_map, coll_ra.find({"address": ""}))))
        # x = coll_ra.update({"id": int(iden)}, {"$set": {"city": cit}})
        # print(x)
        if collection == 'ra':
          res = json.dumps(list(map(add_to_map, coll_ra.find({}, {'_id': 0}))))
        elif collection == 'st':
          res = json.dumps(list(map(add_to_map, coll_st.find({}, {'_id': 0}))))
        elif collection == 'co':
          res = json.dumps(list(map(add_to_map, coll_co.find({}, {'_id': 0}))))
        elif collection == 'ci':
          res = json.dumps(list(map(add_to_map, coll_ci.find({}, {'_id': 0, 'cityngram': 0}))))
        elif collection == 'si':
          res = json.dumps(list(map(add_to_map, coll_si.find({}, {'_id': 0}))))
        elif collection == 'te':
          res = json.dumps(list(map(add_to_map, coll_te.find({}, {'_id': 0}))))
        elif collection == 'bl':
          res = json.dumps(list(map(add_to_map, coll_bl.find({}, {'_id': 0, 'blogdate': 0}))))
        elif collection == 'cp':
          res = json.dumps(list(map(add_to_map, coll_cp.find({}, {'_id': 0}))))
        elif collection == 'telco':
          res = json.dumps(list(map(add_to_map, coll_telco.find({}, {'_id': 0}))))
        elif collection == 'tel':
          res = json.dumps(list(map(add_to_map, coll_tel.find({}, {'_id': 0}))))
        return res
    except Exception as e:
        print(e)
    return res


def get_distinct_column_rows(col):
    return json.dumps(list(map(add_to_map, coll_tel.find({}, {'_id': 0}))))
    
    


