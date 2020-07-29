import pymongo
import re
import json
import datetime
import os
import pprint as pp
from pymongo import MongoClient

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
    else:
        page = r
    print(page)
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
    for i in coll_co.find({'stateid': site_state['id']}):
        site_counties_links += f"""<a class="location-link" href="/locations/{i['statename']}/{i['countyname']}-{i['id']}">{i['countyname'].title()}</a>"""
    site_counties_links += """</div>"""
    comp = re.sub(r'XXsitestateXX', site_state['statename'].title(), comp)
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
            for i in coll_co.find({'stateid': page_state['id']}):
                page_counties_links += f"""<a class="location-link" href="/locations/{i['statename']}/{i['countyname']}-{i['id']}">{i['countyname'].title()}</a>"""
            page_counties_links += """</div>"""
            comp = re.sub(r'XXpagestateXX', page_state['statename'].title(), comp)
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
        elif len(arr) == 5:
            from urllib.parse import unquote
            agents_info = """<div class="registered-agents">"""
            k = arr[3]
            query = re.compile(arr[4], re.IGNORECASE)
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
                print(rt)
        elif re.search(r'^/process-server/', i.route) is not None:
            if re.search(r'^/process-server/id/state', i.route) is not None:
                print(rt)
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
