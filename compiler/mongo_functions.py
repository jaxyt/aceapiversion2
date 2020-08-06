import pymongo
import re
import json
import datetime
import os
import pprint as pp
from pymongo import MongoClient
from similar_text import similar_text

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
    comp = ""
    states_links = """<div class="states-links">"""
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
    for i in coll_st.find():
        states_links +=f"""<a href="/locations/{'-'.join(i['statename'].split(' '))}">{i['statename'].title()}</a>"""
    states_links += "</div>"
    comp += """<!DOCTYPE html><html lang="en"><head>"""
    comp += s.sitemetas if s.sitemetas else t.sitemetas if t.sitemetas else ""
    comp += spage.pagemetas if spage.pagemetas else tpage.pagemetas if tpage.pagemetas else ""
    comp += s.sitelinks if s.sitelinks else t.sitelinks if t.sitelinks else ""
    comp += spage.pagelinks if spage.pagelinks else tpage.pagelinks if tpage.pagelinks else ""
    comp += f"""<title>{spage.title if spage.title else tpage.title if tpage.title else ""}</title>"""
    comp += spage.pagestyle if spage.pagestyle else s.sitestyle if s.sitestyle else tpage.pagestyle if tpage.pagestyle else t.sitestyle if t.sitestyle else ""
    comp += """</head><body>"""
    comp += spage.pageheader if spage.pageheader else s.siteheader if s.siteheader else tpage.pageheader if tpage.pageheader else t.siteheader if t.siteheader else ""
    comp += spage.content if spage.content else tpage.content if tpage.content else ""
    comp += spage.pagefooter if spage.pagefooter else s.sitefooter if s.sitefooter else tpage.pagefooter if tpage.pagefooter else t.sitefooter if t.sitefooter else ""
    comp += s.sitescripts if s.sitescripts else t.sitescripts if t.sitescripts else ""
    comp += spage.pagescripts if spage.pagescripts else tpage.pagescripts if tpage.pagescripts else ""
    comp += """</body></html>"""
    site_counties_links = """<div class="link-list">"""
    site_state = coll_st.find_one({'id': s.location.stateid})
    site_state_acronym = site_state['stateacronym']
    for i in coll_co.find({'stateid': site_state['id']}):
        site_counties_links += f"""<a class="location-link" href="/locations/{i['statename']}/{i['countyname']}-{i['id']}">{i['countyname'].title()}</a>"""
    site_counties_links += """</div>"""
    comp = re.sub(r'XXsitestateXX', site_state['statename'].title(), comp)
    comp = re.sub(r"XXsitestateacronymXX", site_state_acronym, comp)
    comp = re.sub(r'XXsitecountylinksXX', site_counties_links, comp)
    site_cities_links = """<div class="link-list">"""
    site_county = coll_co.find_one({'id': s.location.countyid})
    for i in coll_ci.find({'countyid': site_county['id']}):
        site_cities_links += f"""<a class="location-link" href="/locations/{i['statename']}/{i['countyname']}-{i['countyid']}/{i['cityname']}-{i['id']}">{i['cityname'].title()}</a>"""
    site_cities_links += """</div>"""
    comp = re.sub(r'XXsitecountyXX', site_county['countyname'].title(), comp)
    comp = re.sub(r'XXsitecitylinksXX', site_cities_links, comp)

    site_city = coll_ci.find_one({'id': s.location.cityid})
    comp = re.sub(r'XXsitecityXX', site_city['cityname'].title(), comp)
    comp = re.sub(r'XXstateslinksXX', states_links, comp)
    if arr[1] == "locations":
        page_counties_links = """<div class="link-list">"""
        page_cities_links = """<div class="link-list">"""
        if len(arr) >= 3:
            page_state = coll_st.find_one({'statename': " ".join(arr[2].split('-'))})
            page_state_acronym = page_state['stateacronym']
            for i in coll_co.find({'stateid': page_state['id']}):
                page_counties_links += f"""<a class="location-link" href="/locations/{i['statename']}/{i['countyname']}-{i['id']}">{i['countyname'].title()}</a>"""
            page_counties_links += """</div>"""
            comp = re.sub(r'XXpagestateXX', page_state['statename'].title(), comp)
            comp = re.sub(r'XXpagestateacronymXX', page_state_acronym, comp)
            comp = re.sub(r'XXpagecountylinksXX', page_counties_links, comp)
            if len(arr) >= 4:
                page_county = coll_co.find_one({'id': int(arr[3].split("-")[-1])})
                for i in coll_ci.find({'countyid': page_county['id']}):
                    page_cities_links += f"""<a class="location-link" href="/locations/{i['statename']}/{i['countyname']}-{i['countyid']}/{i['cityname']}-{i['id']}">{i['cityname'].title()}</a>"""
                page_cities_links += """</div>"""
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
            agent = coll_ra.find_one({'id': int(arr[2])})
            agent_info = f"""<div class="registered-agent"><ul id="{agent['id']}" class="agent-container">"""
            agent_info += f"""<li class="company">Company:&nbsp;<a href="/registered-agents/search/company/{agent['company']}">{agent['company'].title()}</a></li>""" if agent['company'] else ""
            agent_info += f"""<li class="agency">Agent:&nbsp;<a href="/registered-agents/search/agency/{agent['agency']}">{agent['agency'].title()}</a></li>""" if agent['agency'] else ""
            agent_info += f"""<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{agent['state']}">{agent['state'].title()}</a></li>""" if agent['state'] else ""
            agent_info += f"""<li class="city">City:&nbsp;<a href="/registered-agents/search/city/{agent['city']}">{agent['city'].title()}</a></li>""" if agent['city'] else ""
            agent_info += f"""<li class="contact-point">Contact:&nbsp;{agent['contact'].title()}</li>""" if agent['contact'] else ""
            agent_info += f"""<li class="address">Address:&nbsp;{agent['address'].title()}</li>""" if agent['address'] else ""
            agent_info += f"""<li class="mail">Mailing Address:&nbsp;{agent['mail'].title()}</li>"""  if agent['mail'] else ""
            agent_info += f"""<li class="ra-phone">Phone:&nbsp;{agent['phone'].title()}</li>""" if agent['phone'] else ""
            agent_info += f"""<li class="fax">Fax:&nbsp;{agent['fax'].title()}</li>""" if agent['fax'] else ""
            agent_info += f"""<li class="email">Email:&nbsp;{agent['email'].title()}</li>""" if agent['email'] else ""
            agent_info += f"""<li class="website">Website:&nbsp;{agent['website'].title()}</li>""" if agent['website'] else ""
            agent_info += "</ul></div>"
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
            agents_info = """<div class="registered-agents">"""
            # k = arr[3]
            # query = re.compile(arr[4], re.IGNORECASE)
            # for i in coll_ra.aggregate([{"$match": {"$or" : [{"company": query},{"agency": query},{"state": query},{"city": query}]}},{"$sort": { k: 1 }}]):
            #     agents_info += f"""<ul id="{i['id']}" class="agent-container">"""
            #     agents_info += f"""<li class="company">Agency:&nbsp;<a href="/registered-agents/search/company/{i['company']}">{i['company'].title()}</a></li>""" if i['company'] else ""
            #     agents_info += f"""<li class="agency">{"Alt-Name" if i["company"] else "Agency"}:&nbsp;<a href="/registered-agents/search/agency/{i['agency']}">{i['agency'].title()}</a></li>""" if i['agency'] else ""
            #     agents_info += f"""<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{i['state']}">{i['state'].title()}</a></li>""" if i['state'] else ""
            #     agents_info += f"""<li class="city">City:&nbsp;<a href="/registered-agents/search/city/{i['city']}">{i['city'].title()}</a></li>""" if i['city'] else ""
            #     agents_info += f"""<li class="contact-point">Contact:&nbsp;{i['contact'].title()}</li>""" if i['contact'] else ""
            #     agents_info += f"""<li class="address">Address:&nbsp;{i['address'].title()}</li>""" if i['address'] else ""
            #     agents_info += f"""<li class="mail">Mailing Address:&nbsp;{i['mail'].title()}</li>""" if i['mail'] else ""
            #     agents_info += f"""<li class="ra-phone">Phone:&nbsp;{i['phone'].title()}</li>""" if i['phone'] else ""
            #     agents_info += f"""<li class="fax">Fax:&nbsp;{i['fax'].title()}</li>""" if i['fax'] else ""
            #     agents_info += f"""<li class="email">Email:&nbsp;{i['email'].title()}</li>""" if i['email'] else ""
            #     agents_info += f"""<li class="website">Website:&nbsp;{i['website'].title()}</li>""" if i['website'] else ""
            #     agents_info += f"""<li class="agent-details"><a href="/registered-agents/{i['id']}"><button>Go to Details</button></a></li>"""
            #     agents_info += "</ul>"
            for k in text_score_search(arr):
                i = k['obj']
                agents_info += f"""<ul id="{i['id']}" class="agent-container">"""
                agents_info += f"""<li class="company">Agency:&nbsp;<a href="/registered-agents/search/company/{i['company']}">{i['company'].title()}</a></li>""" if i['company'] else ""
                agents_info += f"""<li class="agency">{"Alt-Name" if i["company"] else "Agency"}:&nbsp;<a href="/registered-agents/search/agency/{i['agency']}">{i['agency'].title()}</a></li>""" if i['agency'] else ""
                agents_info += f"""<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{i['state']}">{i['state'].title()}</a></li>""" if i['state'] else ""
                agents_info += f"""<li class="city">City:&nbsp;<a href="/registered-agents/search/city/{i['city']}">{i['city'].title()}</a></li>""" if i['city'] else ""
                agents_info += f"""<li class="contact-point">Contact:&nbsp;{i['contact'].title()}</li>""" if i['contact'] else ""
                agents_info += f"""<li class="address">Address:&nbsp;{i['address'].title()}</li>""" if i['address'] else ""
                agents_info += f"""<li class="mail">Mailing Address:&nbsp;{i['mail'].title()}</li>""" if i['mail'] else ""
                agents_info += f"""<li class="ra-phone">Phone:&nbsp;{i['phone'].title()}</li>""" if i['phone'] else ""
                agents_info += f"""<li class="fax">Fax:&nbsp;{i['fax'].title()}</li>""" if i['fax'] else ""
                agents_info += f"""<li class="email">Email:&nbsp;{i['email'].title()}</li>""" if i['email'] else ""
                agents_info += f"""<li class="website">Website:&nbsp;{i['website'].title()}</li>""" if i['website'] else ""
                agents_info += f"""<li class="agent-details"><a href="/registered-agents/{i['id']}"><button>Go to Details</button></a></li>"""
                agents_info += "</ul>"
            agents_info += "</div>"
            comp = re.sub("XXagentsXX", agents_info, comp)
            comp = re.sub("XXagentsqueryXX", arr[4].title(), comp)
    elif arr[1] == "process-server":
        if len(arr) == 3:
            agents_info = """<div class="registered-agents">"""
            corp = coll_cp.find_one({'id': int(arr[2].split("-")[-1])})
            k = corp['searchkey']
            q = corp['searchvalue']
            query = re.compile(q, re.IGNORECASE)
            for i in coll_ra.find({k: query}):
                agents_info += f"""<ul id="{i['id']}" class="agent-container">"""
                agents_info += f"""<li class="company">Company:&nbsp;<a href="/registered-agents/search/company/{i['company']}">{i['company'].title()}</a></li>""" if i['company'] else ""
                agents_info += f"""<li class="agency">Agent:&nbsp;<a href="/registered-agents/search/agency/{i['agency']}">{i['agency'].title()}</a></li>""" if i['agency'] else ""
                agents_info += f"""<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{i['state']}">{i['state'].title()}</a></li>""" if i['state'] else ""
                agents_info += f"""<li class="city">City:&nbsp;<a href="/registered-agents/search/city/{i['city']}">{i['city'].title()}</a></li>""" if i['city'] else ""
                agents_info += f"""<li class="contact-point">Contact:&nbsp;{i['contact'].title()}</li>""" if i['contact'] else ""
                agents_info += f"""<li class="address">Address:&nbsp;{i['address'].title()}</li>""" if i['address'] else ""
                agents_info += f"""<li class="mail">Mailing Address:&nbsp;{i['mail'].title()}</li>""" if i['mail'] else ""
                agents_info += f"""<li class="ra-phone">Phone:&nbsp;{i['phone'].title()}</li>""" if i['phone'] else ""
                agents_info += f"""<li class="fax">Fax:&nbsp;{i['fax'].title()}</li>""" if i['fax'] else ""
                agents_info += f"""<li class="email">Email:&nbsp;{i['email'].title()}</li>""" if i['email'] else ""
                agents_info += f"""<li class="website">Website:&nbsp;{i['website'].title()}</li>""" if i['website'] else ""
                agents_info += f"""<li class="agent-details"><a href="/registered-agents/{i['id']}"><button>Go to Details</button></a></li>"""
                agents_info += "</ul>"
            agents_info += "</div>"
            comp = re.sub('XXagentsXX', agents_info, comp)
            comp = re.sub('XXcorpXX', corp['name'], comp)
            corps_in_states = """<div class="state-corps-links">"""
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
                agents_info += f"""<ul id="{i['id']}" class="agent-container">"""
                agents_info += f"""<li class="company">Company:&nbsp;<a href="/registered-agents/search/company/{i['company']}">{i['company'].title()}</a></li>""" if i['company'] else ""
                agents_info += f"""<li class="agency">Agent:&nbsp;<a href="/registered-agents/search/agency/{i['agency']}">{i['agency'].title()}</a></li>""" if i['agency'] else ""
                agents_info += f"""<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{i['state']}">{i['state'].title()}</a></li>""" if i['state'] else ""
                agents_info += f"""<li class="city">City:&nbsp;<a href="/registered-agents/search/city/{i['city']}">{i['city'].title()}</a></li>""" if i['city'] else ""
                agents_info += f"""<li class="contact-point">Contact:&nbsp;{i['contact'].title()}</li>""" if i['contact'] else ""
                agents_info += f"""<li class="address">Address:&nbsp;{i['address'].title()}</li>""" if i['address'] else ""
                agents_info += f"""<li class="mail">Mailing Address:&nbsp;{i['mail'].title()}</li>""" if i['mail'] else ""
                agents_info += f"""<li class="ra-phone">Phone:&nbsp;{i['phone'].title()}</li>""" if i['phone'] else ""
                agents_info += f"""<li class="fax">Fax:&nbsp;{i['fax'].title()}</li>""" if i['fax'] else ""
                agents_info += f"""<li class="email">Email:&nbsp;{i['email'].title()}</li>""" if i['email'] else ""
                agents_info += f"""<li class="website">Website:&nbsp;{i['website'].title()}</li>""" if i['website'] else ""
                agents_info += f"""<li class="agent-details"><a href="/registered-agents/{i['id']}"><button>Go to Details</button></a></li>"""
                agents_info += "</ul>"
            agents_info += "</div>"
            comp = re.sub('XXagentsXX', agents_info, comp)
            comp = re.sub('XXcorpXX', corp['name'], comp)
            comp = re.sub('XXstatequeryXX', st.title(), comp)
            corps_in_cities = """<div class="state-corps-links">"""
            for i in coll_ra.find({k: query, 'state': state_query, 'city': r".+"}):
                corps_in_cities += f"""<a href="{"/".join(arr)}/{"-".join(i['city'].split(" "))}">{i['city'].title()}</a>"""
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
                agents_info += f"""<ul id="{i['id']}" class="agent-container">"""
                agents_info += f"""<li class="company">Company:&nbsp;<a href="/registered-agents/search/company/{i['company']}">{i['company'].title()}</a></li>""" if i['company'] else ""
                agents_info += f"""<li class="agency">Agent:&nbsp;<a href="/registered-agents/search/agency/{i['agency']}">{i['agency'].title()}</a></li>""" if i['agency'] else ""
                agents_info += f"""<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{i['state']}">{i['state'].title()}</a></li>""" if i['state'] else ""
                agents_info += f"""<li class="city">City:&nbsp;<a href="/registered-agents/search/city/{i['city']}">{i['city'].title()}</a></li>""" if i['city'] else ""
                agents_info += f"""<li class="contact-point">Contact:&nbsp;{i['contact'].title()}</li>""" if i['contact'] else ""
                agents_info += f"""<li class="address">Address:&nbsp;{i['address'].title()}</li>""" if i['address'] else ""
                agents_info += f"""<li class="mail">Mailing Address:&nbsp;{i['mail'].title()}</li>""" if i['mail'] else ""
                agents_info += f"""<li class="ra-phone">Phone:&nbsp;{i['phone'].title()}</li>""" if i['phone'] else ""
                agents_info += f"""<li class="fax">Fax:&nbsp;{i['fax'].title()}</li>""" if i['fax'] else ""
                agents_info += f"""<li class="email">Email:&nbsp;{i['email'].title()}</li>""" if i['email'] else ""
                agents_info += f"""<li class="website">Website:&nbsp;{i['website'].title()}</li>""" if i['website'] else ""
                agents_info += f"""<li class="agent-details"><a href="/registered-agents/{i['id']}"><button>Go to Details</button></a></li>"""
                agents_info += "</ul>"
            agents_info += "</div>"
            comp = re.sub('XXagentsXX', agents_info, comp)
            comp = re.sub('XXcorpXX', corp['name'], comp)
            comp = re.sub('XXstatequeryXX', st.title(), comp)
            comp = re.sub('XXcityqueryXX', cit.title(), comp)
    elif arr[1] == "telecom-agents":
        import urllib.parse
        if len(arr) == 3:
            agent = coll_te.find_one({'id': int(arr[2])})
            agent_info = f"""<div class="registered-agent"><ul id="{agent['id']}" class="agent-container">"""
            agent_info += f"""<li class="carriername">Carrier:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['carriername'])}">{agent['carriername'] if agent['carriername'] else ""}</a></li>"""
            agent_info += f"""<li class="businessname">Business Name:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['businessname'])}">{agent['businessname'] if agent['businessname'] else ""}</a></li>"""
            agent_info += f"""<li class="holdingcompany">Holding Company:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['holdingcompany'])}">{agent['holdingcompany'] if agent['holdingcompany'] else ""}</a></li>"""
            agent_info += f"""<li class="hqaddress">HQ Address:&nbsp;{agent['hqaddress1'] if agent['hqaddress1'] else ""}{", "+agent['hqaddress2'] if agent['hqaddress2'] else ""}{", "+agent['hqaddress3'] if agent['hqaddress3'] else ""}</li>"""
            agent_info += f"""<li class="othertradenames"><ul class="other-trade-names">Other Trade Names""" if agent['othertradename1'] else ""
            agent_info += f"""<li class="othertradenames1"><a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['othertradename1'])}">{agent['othertradename1']}</a></li>""" if agent['othertradename1'] else ""
            agent_info += f"""<li class="othertradenames2"><a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['othertradename2'])}">{agent['othertradename2']}</a></li>""" if agent['othertradename2'] else ""
            agent_info += f"""<li class="othertradenames3"><a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['othertradename3'])}">{agent['othertradename3']}</a></li>""" if agent['othertradename3'] else ""
            agent_info += f"""<li class="othertradenames4"><a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['othertradename4'])}">{agent['othertradename4']}</a></li>""" if agent['othertradename4'] else ""
            agent_info += f"""</ul></li>""" if agent['othertradename1'] else ""
            agent_info += f"""<li class="dcagents"><ul class="dc-agents">DC Agents""" if agent['dcagent1'] else ""
            agent_info += f"""<li class="dcagent1">Agent:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['dcagent1'])}">{agent['dcagent1']}</a></li>""" if agent['dcagent1'] else ""
            agent_info += f"""<li class="dcagent2">Agent Two:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['dcagent2'])}">{agent['dcagent2']}</a></li>""" if agent['dcagent2'] else ""
            agent_info += f"""<li class="dcagentaddress">Address:&nbsp;{agent['dcagentaddress1']}{", "+agent['dcagentaddress2'] if agent['dcagentaddress2'] else ""}{", "+agent['dcagentaddress3'] if agent['dcagentaddress3'] else ""}</li>""" if agent['dcagentaddress1'] else ""
            agent_info += f"""</ul></li>""" if agent['dcagent1'] else ""
            agent_info += f"""<li class="alternateagents"><ul class="alternate-agents">Alternate Agents""" if agent['alternateagent1'] else ""
            agent_info += f"""<li class="alternateagent1">Alt Agent:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['alternateagent1'])}">{agent['alternateagent1']}</a></li>""" if agent['alternateagent1'] else ""
            agent_info += f"""<li class="alternateagent2">Alt Agent:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(agent['alternateagent2'])}">{agent['alternateagent2']}</a></li>""" if agent['alternateagent2'] else ""
            agent_info += f"""<li class="alternateagenttelephone">Phone:&nbsp;{agent['alternateagenttelephone']}</li>""" if agent['alternateagenttelephone'] else ""
            agent_info += f"""<li class="alternateagentext">Ext:&nbsp;{agent['alternateagentext']}</li>""" if agent['alternateagentext'] else ""
            agent_info += f"""<li class="alternateagentfax">Fax:&nbsp;{agent['alternateagentfax']}</li>""" if agent['alternateagentfax'] else ""
            agent_info += f"""<li class="alternateagentemail">Email:&nbsp;{agent['alternateagentemail']}</li>""" if agent['alternateagentemail'] else ""
            agent_info += f"""<li class="alternateagentaddress">Address:&nbsp;{agent['alternateagentaddress1']}{", "+agent['alternateagentaddress2'] if agent['alternateagentaddress2'] else ""}{", "+agent['alternateagentaddress3'] if agent['alternateagentaddress3'] else ""}{", "+agent['alternateagentcity'] if agent['alternateagentcity'] else ""}{", "+agent['alternateagentstate'] if agent['alternateagentstate'] else ""}{", "+agent['alternateagent1zip'] if agent['alternateagent1zip'] else ""}</li>""" if agent['alternateagentaddress1'] else ""
            agent_info += f"""<ul><li>""" if agent['alternateagent1'] else ""
            agent_info += f"""<li class="notes"><ul class="other-trade-names">Notes""" if agent['note1'] else ""
            agent_info += f"""<li class="note1">{agent['note1']}</li>""" if agent['note1'] else ""
            agent_info += f"""<li class="note2">{agent['note2']}</li>""" if agent['note2'] else ""
            agent_info += f"""<li class="note3">{agent['note3']}</li>""" if agent['note3'] else ""
            agent_info += f"""</ul></li>""" if agent['note1'] else ""
            agent_info += "</ul></div>"
            comp = re.sub("XXagentXX", agent_info, comp)
        elif len(arr) == 5:
            agents_info = """<div class="registered-agents">"""
            k = arr[3]
            query = re.compile(arr[4], re.IGNORECASE)
            for i in coll_te.aggregate([{"$match": {"$or" : [{"carriername": query},{"businessname": query},{"holdingcompany": query},{"othertradename1": query},{"othertradename2": query},{"othertradename3": query},{"othertradename4": query},{"dcagent1": query},{"dcagent2": query},{"alternateagent1": query},{"alternateagent2": query}]}},{"$sort": { k: 1 }}]):
                agents_info += f"""<ul id="{i['id']}" class="agent-container">"""
                agents_info += f"""<li class="carriername">Carrier:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['carriername'])}">{i['carriername'] if i['carriername'] else ""}</a></li>"""
                agents_info += f"""<li class="businessname">Business Name:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['businessname'])}">{i['businessname'] if i['businessname'] else ""}</a></li>"""
                agents_info += f"""<li class="holdingcompany">Holding Company:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['holdingcompany'])}">{i['holdingcompany'] if i['holdingcompany'] else ""}</a></li>"""
                agents_info += f"""<li class="hqaddress">HQ Address:&nbsp;{i['hqaddress1'] if i['hqaddress1'] else ""}{", "+i['hqaddress2'] if i['hqaddress2'] else ""}{", "+i['hqaddress3'] if i['hqaddress3'] else ""}</li>"""
                agents_info += f"""<li class="othertradenames"><ul class="other-trade-names">Other Trade Names""" if i['othertradename1'] else ""
                agents_info += f"""<li class="othertradenames1"><a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['othertradename1'])}">{i['othertradename1']}</a></li>""" if i['othertradename1'] else ""
                agents_info += f"""<li class="othertradenames2"><a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['othertradename2'])}">{i['othertradename2']}</a></li>""" if i['othertradename2'] else ""
                agents_info += f"""<li class="othertradenames3"><a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['othertradename3'])}">{i['othertradename3']}</a></li>""" if i['othertradename3'] else ""
                agents_info += f"""<li class="othertradenames4"><a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['othertradename4'])}">{i['othertradename4']}</a></li>""" if i['othertradename4'] else ""
                agents_info += f"""</ul></li>""" if i['othertradename1'] else ""
                agents_info += f"""<li class="dcagent1">Agent:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['dcagent1'])}">{i['dcagent1']}</a></li>""" if i['dcagent1'] else ""
                agents_info += f"""<li class="dcagent2">Agent Two:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['dcagent2'])}">{i['dcagent2']}</a></li>""" if i['dcagent2'] else ""
                agents_info += f"""<li class="alternateagent1">Alt Agent:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['alternateagent1'])}">{i['alternateagent1']}</a></li>""" if i['alternateagent1'] else ""
                agents_info += f"""<li class="alternateagent2">Alt Agent Two:&nbsp;<a href="/telecom-agents/search/carriername/{urllib.parse.quote(i['alternateagent2'])}">{i['alternateagent2']}</a></li>""" if i['alternateagent2'] else ""
                agents_info += f"""<li class="agent-details"><a href="/registered-agents/{i['id']}"><button>Go to Details</button></a></li>"""
                agents_info += "</ul>"
            agents_info += "</div>"
            comp = re.sub("XXagentsXX", agents_info, comp)
            comp = re.sub("XXagentsqueryXX", arr[4].title(), comp)
    corp_links = """<div class="corp-links">"""
    for i in coll_cp.find():
        corp_links += f"""<a href="/process-server/{"-".join(i['searchvalue'].split(" "))}-{i['id']}">{i['name']}</a>"""
    corp_links += """</div>"""
    html_sitemap = """<div><ul class="sitemap-links">"""
    for i in s.pages:
        if re.search(r'(/locations)|(/registered-agents)|(/process-server)|(/blog/posts/id)|(\.)', i.route) is None:
            if i.route == "/":
                html_sitemap += """<li><a href="/">Home</a></li>"""
            else:
                html_sitemap += f"""<li><a href="{i.route}">{" ".join(i.route.split("/")).title()}</a></li>"""
    html_sitemap += """</ul></div>"""
    comp = re.sub('XXsitemapXX', html_sitemap, comp)
    comp = re.sub('XXcorplinksXX', corp_links, comp)
    comp = re.sub('XXsitenameXX', s.sitename if s.sitename else "", comp)
    comp = re.sub('XXspagetitleXX', spage.title if spage.title else "", comp)
    comp = re.sub('XXspagerouteXX', spage.route if spage.route else "", comp)
    comp = re.sub('XXtemplatenameXX', t.templatename if t.templatename else "", comp)
    comp = re.sub('XXtpagetitleXX', tpage.title if tpage.title else "", comp)
    comp = re.sub('XXtpagerouteXX', tpage.route if tpage.route else "", comp)
    comp = re.sub(r'Ct ', "CT ", comp)
    comp = re.sub(r'Csc ', "CSC ", comp)
    comp = re.sub(r'Nrai ', "NRAI ", comp)
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
    url_cnt = 0
    sitemap = """<?xml version="1.0" encoding="utf-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">"""
    for i in s.pages:
        if re.search(r'^/locations/', i.route) is not None:
            if len(i.route.split("/")) == 3:
                for n in coll_st.find():
                    sitemap_urls.append(f"""<url><loc>https://www.{s.sitename}.com/locations/{n['statename']}</loc></url>""")
                    url_cnt += 1
            elif len(i.route.split("/")) == 5:
                for n in coll_ci.find():
                    sitemap_urls.append(f"""<url><loc>https://www.{s.sitename}.com/locations/{n['statename']}/{n['countyname']}-{n['countyid']}/{n['cityname']}-{n['id']}</loc></url>""")
                    url_cnt += 1
        elif re.search(r'^/blog/', i.route) is not None:
            if len(i.route.split("/")) == 3:
                sitemap_urls.append(f"""<url><loc>https://www.{s.sitename}.com{i.route}</loc></url>""")
                url_cnt += 1
            elif len(i.route.split("/")) == 4:
                for n in coll_bl.find({'blogcategory': s.blogcategory}):
                    sitemap_urls.append(f"""<url><loc>https://www.{s.sitename}.com/blog/posts/{n['bloguri'] if n['bloguri'] else ""}-{n['id']}</loc></url>""")
                    url_cnt += 1
        elif re.search(r'^/registered-agents/', i.route) is not None:
            if re.search(r'^/registered-agents/search', i.route) is not None:
                import urllib.parse
                for n in ["company", "agency", "state", "city"]:
                    for k in coll_ra.find().distinct(n):
                        sitemap_urls.append(f"<url><loc>https://www.{s.sitename}.com"+urllib.parse.quote(f"""/registered-agents/search/{n}/{k.lower()}""")+"</loc></url>")
                        url_cnt += 1
            else:
                for n in coll_ra.find():
                    sitemap_urls.append(f"""<url><loc>https://www.{s.sitename}.com/registered-agents/{n['id']}</loc></url>""")
                    url_cnt += 1
        elif re.search(r'^/process-server/', i.route) is not None:
            if re.search(r'^/process-server/id/state', i.route) is not None:
                for n in coll_cp.find():
                    sitemap_urls.append(f"""<url><loc>https://www.{s.sitename}.com/process-server/{"-".join(n['name'].split(" ")).lower()}-{n['id']}</loc></url>""")
                    url_cnt += 1
                    for k in coll_ra.find().distinct("state"):
                        sitemap_urls.append(f"""<url><loc>https://www.{s.sitename}.com/process-server/{"-".join(n['name'].split(" ")).lower()}-{n['id']}/{"-".join(k.split(" ")).lower()}</loc></url>""")
                        url_cnt += 1
        else:
            if re.search(r'\.[a-z]{2,4}$', i.route) is None:
                sitemap_urls.append(f"""<url><loc>https://www.{s.sitename}.com{i.route}</loc></url>""")
                url_cnt += 1
    if rt == "/sitemap.xml":
        for idx, val in enumerate(sitemap_urls):
            if idx < 50000:
                sitemap += val
            else:
                break
    else:
        multiplier = int(re.match(r'[0-9]+', rt)[0])
        end = (multiplier*50000)
        start = (multiplier-1)*50000
        for idx, val in enumerate(sitemap_urls):
            if idx < end and idx >= start:
                sitemap += val
            elif idx >= end:
                break
    sitemap += """</urlset>"""
    print(url_cnt)
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
