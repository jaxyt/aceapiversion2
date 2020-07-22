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
        states_links += """<a href="/locations/{}">{}</a>""".format('-'.join(i['statename'].split(' ')), i['statename'].title())
    states_links += "</div>"
    comp += """<!DOCTYPE html><html lang="en"><head>"""
    comp += s.sitemetas if s.sitemetas else t.sitemetas if t.sitemetas else ""
    comp += spage.pagemetas if spage.pagemetas else tpage.pagemetas if tpage.pagemetas else ""
    comp += s.sitelinks if s.sitelinks else t.sitelinks if t.sitelinks else ""
    comp += spage.pagelinks if spage.pagelinks else tpage.pagelinks if tpage.pagelinks else ""
    comp += """<title>{}</title>""".format(spage.title if spage.title else tpage.title if tpage.title else "")
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
        site_counties_links += """<a class="location-link" href="/locations/{}/{}-{}">{}</a>""".format(i['statename'],
                                                                                                       i['countyname'],
                                                                                                       i['id'],
                                                                                                       i['countyname'].title())
    site_counties_links += """</div>"""
    comp = re.sub(r'XXsitestateXX', site_state['statename'].title(), comp)
    comp = re.sub(r'XXsitecountylinksXX', site_counties_links, comp)
    site_cities_links = """<div class="link-list">"""
    site_county = coll_co.find_one({'id': s.location.countyid})
    for i in coll_ci.find({'countyid': site_county['id']}):
        site_cities_links += """<a class="location-link" href="/locations/{}/{}-{}/{}-{}">{}</a>""".format(i['statename'],
                                                                                                           i['countyname'],
                                                                                                           i['countyid'],
                                                                                                           i['cityname'],
                                                                                                           i['id'],
                                                                                                           i['cityname'].title())
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
                page_counties_links += """<a class="location-link" href="/locations/{}/{}-{}">{}</a>""".format(i['statename'], i['countyname'], i['id'], i['countyname'].title())
            page_counties_links += """</div>"""
            comp = re.sub(r'XXpagestateXX', page_state['statename'].title(), comp)
            comp = re.sub(r'XXpagecountylinksXX', page_counties_links, comp)
            if len(arr) >= 4:
                page_county = coll_co.find_one({'id': int(arr[3].split("-")[-1])})
                for i in coll_ci.find({'countyid': page_county['id']}):
                    page_cities_links += """<a class="location-link" href="/locations/{}/{}-{}/{}-{}">{}</a>""".format(i['statename'], i['countyname'], i['countyid'], i['cityname'], i['id'], i['cityname'].title())
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
                snippets += """<div class="snippet"><h3><a href="/blog/posts/{}-{}">{}</a></h3><p>{}</p></div>""".format("-".join(i['bloguri'].split(" ")), i['id'], i['blogtitle'].title(), post)
            snippets += "</div>"
            comp = re.sub('XXsnippetsXX', snippets, comp)
        elif len(arr) == 4:
            blog_post = coll_bl.find_one({'id': int(arr[3].split('-')[-1])})
            post = ""
            if s.national == False:
                post = blog_post['blogpost']
            else:
                post = blog_post['blogpostnational']
            post_template = """<div class="blog-post"><h1>{}</h1><div><span>{}</span><br><span>{}</span></div><p>{}</p></div>""".format(blog_post['blogtitle'].title(), blog_post['blogdate'], blog_post['blogauthor'], post)
            comp = re.sub('XXblogpostXX', post_template, comp)
            comp = re.sub('XXblogtitleXX', blog_post['blogtitle'] if blog_post['blogtitle'] else "", comp)
            comp = re.sub('XXbloguriXX', blog_post['bloguri'] if blog_post['bloguri'] else "", comp)
            comp = re.sub('XXblogcategoryXX', blog_post['blogcategory'] if blog_post['blogcategory'] else "", comp)
            comp = re.sub('XXblogkeywordsXX', blog_post['blogkeywords'] if blog_post['blogkeywords'] else "", comp)
            comp = re.sub('XXblogpostlocalXX', blog_post['blogpost'] if blog_post['blogpost'] else "", comp)
            comp = re.sub('XXblogpostnationalXX', blog_post['blogpostnational'] if blog_post['blogpostnational'] else "", comp)
            comp = re.sub('XXblogdateXX', blog_post['blogdate'] if blog_post['blogdate'] else "", comp)
            comp = re.sub('XXblogauthorXX', blog_post['blogauthor'] if blog_post['blogauthor'] else "", comp)
    elif arr[1] == "registered-agents":
        if len(arr) == 3:
            agent = coll_ra.find_one({'id': int(arr[2])})
            agent_info = """<div class="registered-agent"><ul id="{}" class="agent-container">""".format(agent['id'])
            agent_info += """<li class="agency">Agency:&nbsp;<a href="/registered-agents/search/agency/{}">{}</a></li>""".format(
                agent['agency'], agent['agency'].title()) if agent['agency'] else ""
            agent_info += """<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{}">{}</a></li>""".format(
                agent['state'], agent['state'].title()) if agent['state'] else ""
            agent_info += """<li class="company">Company:&nbsp;<a href="/registered-agents/search/company/{}">{}</a></li>""".format(
                agent['company'], agent['company'].title()) if agent['company'] else ""
            agent_info += """<li class="contact-point">Contact:&nbsp;{}</li>""".format(
                agent['contact'].title()) if agent['contact'] else ""
            agent_info += """<li class="address">Address:&nbsp;{}</li>""".format(
                agent['address'].title()) if agent['address'] else ""
            agent_info += """<li class="mail">Mailing Address:&nbsp;{}</li>""".format(
                agent['mail'].title()) if agent['mail'] else ""
            agent_info += """<li class="ra-phone">Phone:&nbsp;{}</li>""".format(
                agent['phone'].title()) if agent['phone'] else ""
            agent_info += """<li class="fax">Fax:&nbsp;{}</li>""".format(
                agent['fax'].title()) if agent['fax'] else ""
            agent_info += """<li class="email">Email:&nbsp;{}</li>""".format(
                agent['email'].title()) if agent['email'] else ""
            agent_info += """<li class="website">Website:&nbsp;{}</li>""".format(
                agent['website'].title()) if agent['website'] else ""
            agent_info += "</ul></div>"
            comp = re.sub("XXagentXX", agent_info, comp)
        elif len(arr) == 5:
            from urllib.parse import unquote
            agents_info = """<div class="registered-agents">"""
            k = arr[3]
            query = re.compile(arr[4], re.IGNORECASE)
            for i in coll_ra.find({k: query}):
                agents_info += """<ul id="{}" class="agent-container">""".format(i['id'])
                agents_info += """<li class="agency">Agency:&nbsp;<a href="/registered-agents/search/agency/{}">{}</a></li>""".format(
                    i['agency'], i['agency'].title()) if i['agency'] else ""
                agents_info += """<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{}">{}</a></li>""".format(
                    i['state'], i['state'].title()) if i['state'] else ""
                agents_info += """<li class="company">Company:&nbsp;<a href="/registered-agents/search/company/{}">{}</a></li>""".format(
                    i['company'], i['company'].title()) if i['company'] else ""
                agents_info += """<li class="contact-point">Contact:&nbsp;{}</li>""".format(
                    i['contact'].title()) if i['contact'] else ""
                agents_info += """<li class="address">Address:&nbsp;{}</li>""".format(
                    i['address'].title()) if i['address'] else ""
                agents_info += """<li class="mail">Mailing Address:&nbsp;{}</li>""".format(
                    i['mail'].title()) if i['mail'] else ""
                agents_info += """<li class="ra-phone">Phone:&nbsp;{}</li>""".format(
                    i['phone'].title()) if i['phone'] else ""
                agents_info += """<li class="fax">Fax:&nbsp;{}</li>""".format(
                    i['fax'].title()) if i['fax'] else ""
                agents_info += """<li class="email">Email:&nbsp;{}</li>""".format(
                    i['email'].title()) if i['email'] else ""
                agents_info += """<li class="website">Website:&nbsp;{}</li>""".format(
                    i['website'].title()) if i['website'] else ""
                agents_info += "</ul>"
            agents_info += "</div>"
            comp = re.sub("XXagentsXX", agents_info, comp)
    elif arr[1] == "process-server":
        if len(arr) == 3:
            agents_info = """<div class="registered-agents">"""
            print(int(arr[2].split("-")[-1]))
            corp = coll_cp.find_one({'id': int(arr[2].split("-")[-1])})
            print(corp)
            k = corp['searchkey']
            q = corp['searchvalue']
            print(k)
            print(q)
            query = re.compile(q, re.IGNORECASE)
            print(query)
            for i in coll_ra.find({k: query}):
                print(i)
                agents_info += """<ul id="{}" class="agent-container">""".format(i['id'])
                agents_info += """<li class="agency">Agency:&nbsp;<a href="/registered-agents/search/agency/{}">{}</a></li>""".format(
                    i['agency'], i['agency'].title()) if i['agency'] else ""
                agents_info += """<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{}">{}</a></li>""".format(
                    i['state'], i['state'].title()) if i['state'] else ""
                agents_info += """<li class="company">Company:&nbsp;<a href="/registered-agents/search/company/{}">{}</a></li>""".format(
                    i['company'], i['company'].title()) if i['company'] else ""
                agents_info += """<li class="contact-point">Contact:&nbsp;{}</li>""".format(
                    i['contact'].title()) if i['contact'] else ""
                agents_info += """<li class="address">Address:&nbsp;{}</li>""".format(
                    i['address'].title()) if i['address'] else ""
                agents_info += """<li class="mail">Mailing Address:&nbsp;{}</li>""".format(
                    i['mail'].title()) if i['mail'] else ""
                agents_info += """<li class="ra-phone">Phone:&nbsp;{}</li>""".format(
                    i['phone'].title()) if i['phone'] else ""
                agents_info += """<li class="fax">Fax:&nbsp;{}</li>""".format(
                    i['fax'].title()) if i['fax'] else ""
                agents_info += """<li class="email">Email:&nbsp;{}</li>""".format(
                    i['email'].title()) if i['email'] else ""
                agents_info += """<li class="website">Website:&nbsp;{}</li>""".format(
                    i['website'].title()) if i['website'] else ""
                agents_info += "</ul>"
            agents_info += "</div>"
            comp = re.sub('XXagentsXX', agents_info, comp)
            comp = re.sub('XXcorpXX', corp['name'], comp)
            corps_in_states = """<div class="state-corps-links">"""
            for i in coll_st.find():
                corps_in_states += """<a href="{}/{}">{}</a>""".format("/".join(arr), "-".join(i['statename'].split(" ")), i['statename'].title())
            corps_in_states += """</div>"""
            comp = ('XXcorpsinstatesXX', corps_in_states, comp)
        elif len(arr) == 4:
            agents_info = """<div class="registered-agents">"""
            corp = coll_cp.find_one({'id': int(arr[2].split("-")[-1])})
            st = " ".join(arr[3].split("-"))
            k = corp['searchkey']
            q = corp['searchvalue']
            query = re.compile(q, re.IGNORECASE)
            state_query = re.compile(st.lower(), re.IGNORECASE)
            for i in coll_ra.find({k: query, 'state': state_query}):
                agents_info += """<ul id="{}" class="agent-container">""".format(i['id'])
                agents_info += """<li class="agency">Agency:&nbsp;<a href="/registered-agents/search/agency/{}">{}</a></li>""".format(
                    i['agency'], i['agency'].title()) if i['agency'] else ""
                agents_info += """<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{}">{}</a></li>""".format(
                    i['state'], i['state'].title()) if i['state'] else ""
                agents_info += """<li class="company">Company:&nbsp;<a href="/registered-agents/search/company/{}">{}</a></li>""".format(
                    i['company'], i['company'].title()) if i['company'] else ""
                agents_info += """<li class="contact-point">Contact:&nbsp;{}</li>""".format(
                    i['contact'].title()) if i['contact'] else ""
                agents_info += """<li class="address">Address:&nbsp;{}</li>""".format(
                    i['address'].title()) if i['address'] else ""
                agents_info += """<li class="mail">Mailing Address:&nbsp;{}</li>""".format(
                    i['mail'].title()) if i['mail'] else ""
                agents_info += """<li class="ra-phone">Phone:&nbsp;{}</li>""".format(
                    i['phone'].title()) if i['phone'] else ""
                agents_info += """<li class="fax">Fax:&nbsp;{}</li>""".format(
                    i['fax'].title()) if i['fax'] else ""
                agents_info += """<li class="email">Email:&nbsp;{}</li>""".format(
                    i['email'].title()) if i['email'] else ""
                agents_info += """<li class="website">Website:&nbsp;{}</li>""".format(
                    i['website'].title()) if i['website'] else ""
                agents_info += "</ul>"
            agents_info += "</div>"
            comp = re.sub('XXagentsXX', agents_info, comp)
            comp = re.sub('XXcorpXX', corp['name'], comp)
            comp = re.sub('XXstateXX', st.title(), comp)
    corp_links = """<div class="corp-links">"""
    for i in coll_cp.find():
        corp_links += """<a href="/process-server/{}-{}">{}</a>""".format(i['searchvalue'], i['id'], i['name'])
    corp_links += """</div>"""
    comp = re.sub('XXcorplinksXX', corp_links, comp)
    comp = re.sub('XXsitenameXX', s.sitename if s.sitename else "", comp)
    comp = re.sub('XXspagetitleXX', spage.title if spage.title else "", comp)
    comp = re.sub('XXspagerouteXX', spage.route if spage.route else "", comp)
    comp = re.sub('XXtemplatenameXX', t.templatename if t.templatename else "", comp)
    comp = re.sub('XXtpagetitleXX', tpage.title if tpage.title else "", comp)
    comp = re.sub('XXtpagerouteXX', tpage.route if tpage.route else "", comp)
    comp = replace_shortcodes(s, t, comp)
    comp = replace_shortcodes(s, t, comp)
    return comp



def replace_shortcodes(site, template, string_content):
    compiled = string_content
    for i in site.shortcodes:
        reg = re.compile("""XX{}XX""".format(i.name))
        compiled = re.sub(reg, i.value, compiled)
    for i in template.shortcodes:
        reg = re.compile("""XX{}XX""".format(i.name))
        compiled = re.sub(reg, i.value, compiled)
    return compiled



def render_xml_sitemap(s, t):
    sitemap = """<?xml version="1.0" encoding="utf-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">"""
    for i in s.pages:
        if re.search(r'^/locations/', i.route) is not None:
            if len(i.route.split("/")) == 3:
                for n in coll_st.find():
                    sitemap += """<url><loc>https://www.{}.com/locations/{}</loc></url>""".format(s.sitename, n['statename'])
            elif len(i.route.split("/")) == 5:
                for n in coll_ci.find():
                    sitemap += """<url><loc>https://www.{}.com/locations/{}/{}-{}/{}-{}</loc></url>""".format(s.sitename, n['statename'], n['countyname'], n['countyid'], n['cityname'], n['id'])
        elif re.search(r'^/blog/', i.route) is not None:
            if len(i.route.split("/")) == 3:
                sitemap += """<url><loc>https://www.{}.com{}</loc></url>""".format(s.sitename, i.route)
            elif len(i.route.split("/")) == 4:
                for n in coll_bl.find({'blogcategory': s.blogcategory}):
                    sitemap += """<url><loc>https://www.{}.com/blog/posts/{}-{}</loc></url>""".format(s.sitename, n['bloguri'] if n['bloguri'] else "", n['id'])
        elif re.search(r'^/registered-agents/', i.route) is not None:
            if re.search(r'^/registered-agents/search', i.route) is None:
                for n in coll_ra.find():
                    sitemap += """<url><loc>https://www.{}.com/registered-agents/{}</loc></url>""".format(s.sitename, n['id'])
        else:
            if re.search(r'\.[a-z]{2,4}$', i.route) is None:
                sitemap += """<url><loc>https://www.{}.com{}</loc></url>""".format(s.sitename, i.route)
    sitemap += """</urlset>"""
    return sitemap
