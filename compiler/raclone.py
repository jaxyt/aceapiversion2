import pymongo
import re
import json
import datetime
import os
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
coll_tel = db.registeredagents_telecomcorps


def compiler_v4(s, t, r, arr):
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
            agent = coll_ra.find_one({'id': int(arr[2])})
            agent_info = "".join([
                f"""<div class="registered-agent"><ul id="{agent['id']}" class="agent-container">""",
                f"""<li class="company">Company:&nbsp;<a href="/registered-agents/search/company/{agent['company']}">{agent['company'].title()}</a></li>""" if agent['company'] else "",
                f"""<li class="agency">Agent:&nbsp;<a href="/registered-agents/search/agency/{agent['agency']}">{agent['agency'].title()}</a></li>""" if agent['agency'] else "",
                f"""<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{agent['state']}">{agent['state'].title()}</a></li>""" if agent['state'] else "",
                f"""<li class="city">City:&nbsp;<a href="/registered-agents/search/city/{agent['city']}">{agent['city'].title()}</a></li>""" if agent['city'] else "",
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
            agents_info = """<div class="registered-agents">"""
            k = arr[3]
            q = arr[4]
            q = re.sub(r'[^\w\s]','',q)
            q = re.sub(r'\s{2,}','',q)
            q = q.strip(" ")
            q = "|".join(q.split(" "))
            print(q)
            query = re.compile(q, re.IGNORECASE)
            for i in coll_ra.aggregate([{"$match": {"$or" : [{"company": query},{"state": query},{"agency": query},{"address": query},{"website": query},{"city": query}]}},{"$sort": { k: 1 }}]):
                agents_info += "".join([
                    f"""<ul id="{i['id']}" class="agent-container">""",
                    f"""<li class="company">Agency:&nbsp;<a href="/registered-agents/search/company/{i['company']}">{i['company'].title()}</a></li>""" if i['company'] else "",
                    f"""<li class="agency">{"Alt-Name" if i["company"] else "Agency"}:&nbsp;<a href="/registered-agents/search/agency/{i['agency']}">{i['agency'].title()}</a></li>""" if i['agency'] else "",
                    f"""<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{i['state']}">{i['state'].title()}</a></li>""" if i['state'] else "",
                    f"""<li class="city">City:&nbsp;<a href="/registered-agents/search/city/{i['city']}">{i['city'].title()}</a></li>""" if i['city'] else "",
                    f"""<li class="address">Address:&nbsp;{i['address'].title()}</li>""" if i['address'] else "",
                    f"""<li class="agent-details"><a href="/registered-agents/{i['id']}"><button>Go to Details</button></a></li>""",
                    "</ul>"
                ])
            agents_info += "</div>"
            comp = re.sub("XXagentsXX", agents_info, comp)
            comp = re.sub("XXagentsqueryXX", arr[4].title(), comp)
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
                agents_info += "".join([
                    f"""<ul id="{i['id']}" class="agent-container">""",
                    f"""<li class="company">Agent:&nbsp;<a href="/registered-agents/search/company/{i['company']}">{i['company'].title()}</a></li>""" if i['company'] else "",
                    f"""<li class="agency">{"Alt-Name" if i['company'] else "Agent"}:&nbsp;<a href="/registered-agents/search/agency/{i['agency']}">{i['agency'].title()}</a></li>""" if i['agency'] else "",
                    f"""<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{i['state']}">{i['state'].title()}</a></li>""" if i['state'] else "",
                    f"""<li class="city">City:&nbsp;<a href="/registered-agents/search/city/{i['city']}">{i['city'].title()}</a></li>""" if i['city'] else "",
                    f"""<li class="contact-point">Contact:&nbsp;{i['contact'].title()}</li>""" if i['contact'] else "",
                    f"""<li class="address">Address:&nbsp;{i['address'].title()}</li>""" if i['address'] else "",
                    f"""<li class="mail">Mailing Address:&nbsp;{i['mail'].title()}</li>""" if i['mail'] else "",
                    f"""<li class="ra-phone">Phone:&nbsp;{i['phone'].title()}</li>""" if i['phone'] else "",
                    f"""<li class="fax">Fax:&nbsp;{i['fax'].title()}</li>""" if i['fax'] else "",
                    f"""<li class="email">Email:&nbsp;{i['email'].title()}</li>""" if i['email'] else "",
                    f"""<li class="website">Website:&nbsp;{i['website'].title()}</li>""" if i['website'] else "",
                    f"""<li class="agent-details"><a href="/registered-agents/{i['id']}"><button>Go to Details</button></a></li>""",
                    "</ul>"
                ])
            agents_info += "</div>"
            comp = re.sub('XXagentsXX', agents_info, comp)
            comp = re.sub('XXstatequeryXX', st.title(), comp)
            corps_in_cities = """<div class="state-corps-links">"""
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
                agents_info += "".join([
                    f"""<ul id="{i['id']}" class="agent-container">""",
                    f"""<li class="company">Agent:&nbsp;<a href="/registered-agents/search/company/{i['company']}">{i['company'].title()}</a></li>""" if i['company'] else "",
                    f"""<li class="agency">{"Alt-Name" if i['company'] else "Agent"}:&nbsp;<a href="/registered-agents/search/agency/{i['agency']}">{i['agency'].title()}</a></li>""" if i['agency'] else "",
                    f"""<li class="state">State:&nbsp;<a href="/registered-agents/search/state/{i['state']}">{i['state'].title()}</a></li>""" if i['state'] else "",
                    f"""<li class="city">City:&nbsp;<a href="/registered-agents/search/city/{i['city']}">{i['city'].title()}</a></li>""" if i['city'] else "",
                    f"""<li class="contact-point">Contact:&nbsp;{i['contact'].title()}</li>""" if i['contact'] else "",
                    f"""<li class="address">Address:&nbsp;{i['address'].title()}</li>""" if i['address'] else "",
                    f"""<li class="mail">Mailing Address:&nbsp;{i['mail'].title()}</li>""" if i['mail'] else "",
                    f"""<li class="ra-phone">Phone:&nbsp;{i['phone'].title()}</li>""" if i['phone'] else "",
                    f"""<li class="fax">Fax:&nbsp;{i['fax'].title()}</li>""" if i['fax'] else "",
                    f"""<li class="email">Email:&nbsp;{i['email'].title()}</li>""" if i['email'] else "",
                    f"""<li class="website">Website:&nbsp;{i['website'].title()}</li>""" if i['website'] else "",
                    f"""<li class="agent-details"><a href="/registered-agents/{i['id']}"><button>Go to Details</button></a></li>""",
                    "</ul>"
                ])
            agents_info += "</div>"
            comp = re.sub('XXagentsXX', agents_info, comp)
            comp = re.sub('XXstatequeryXX', st.title(), comp)
            comp = re.sub('XXcityqueryXX', cit.title(), comp)
    html_sitemap = """<div><ul class="sitemap-links">"""
    for i in s.pages:
        if re.search(r'(^/locations)|(^/registered-agents)|(^/telecom-agents)|(^/process-server)|(/blog/posts/id)|(^/agents-by-state/)|(\.)', i.route) is None:
            if i.route == "/":
                html_sitemap += """<li><a href="/">Home</a></li>"""
            else:
                html_sitemap += f"""<li><a href="{i.route}">{" ".join(i.route.split("/")).title()}</a></li>"""
    html_sitemap += """</ul></div>"""
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
                sitemap_urls.append("".join(list(map(lambda n: f"""<url><loc>https://www.{s.sitename}.com/registered-agents/{n['id']}</loc></url>""", coll_ra.find()))))
        elif re.search(r'^/telecom-agents/', i.route) is not None:
            if re.search(r'^/telecom-agents/search', i.route) is not None:
                import urllib.parse
                for n in ['carriername', 'businessname', 'holdingcompany', 'othertradename1', 'othertradename2', 'othertradename3', 'othertradename4', 'dcagent1', 'dcagent2', 'dcagentcity', 'dcagentstate']:
                    sitemap_urls.append("".join(list(map(lambda k: "".join([f"""<url><loc>https://www.{s.sitename}.com""", urllib.parse.quote(f"""/telecom-agents/search/{n}/{k.lower()}"""), "</loc></url>"]), coll_tel.find().distinct(n)))))
            else:
                sitemap_urls.append("".join(list(map(lambda n: f"""<url><loc>https://www.{s.sitename}.com/telecom-agents/{n['id']}</loc></url>""", coll_tel.find()))))
        elif re.search(r'^/process-server/', i.route) is not None:
            if re.search(r'^/process-server/id/state/city', i.route) is not None:
                # nested map lambda functions to get all three layers of permutated dynamic url routes simultaneously
                sitemap_urls.append("".join(list(map(lambda n: "".join([f"""<url><loc>https://www.{s.sitename}.com/process-server/{"-".join(n['name'].split(" ")).lower()}-{n['id']}</loc></url>""", "".join(list(map(lambda k: "".join([f"""<url><loc>https://www.{s.sitename}.com/process-server/{"-".join(n['name'].split(" ")).lower()}-{n['id']}/{"-".join(k.split(" ")).lower()}</loc></url>""", "".join(list(map(lambda m: f"""<url><loc>https://www.{s.sitename}.com/process-server/{"-".join(n['name'].split(" ")).lower()}-{n['id']}/{"-".join(k.split(" ")).lower()}/{"-".join(m.split(" ")).lower()}</loc></url>""", coll_ra.find({'state': k}).distinct('city'))))]), coll_ra.find().distinct("state"))))]), coll_cp.find()))))
        else:
            if re.search(r'\.[a-z]{2,4}$', i.route) is None:
                sitemap_urls.append(f"""<url><loc>https://www.{s.sitename}.com{i.route}</loc></url>""")
    sitemap = "".join(["""<?xml version="1.0" encoding="utf-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">""", "".join(sitemap_urls), """</urlset>"""])
    return sitemap





def replace_shortcodes(site, template, string_content):
    compiled = string_content
    for i in site.shortcodes:
        reg = re.compile(f"""XX{i.name}XX""")
        compiled = re.sub(reg, i.value, compiled)
    for i in template.shortcodes:
        reg = re.compile(f"""XX{i.name}XX""")
        compiled = re.sub(reg, i.value, compiled)
    return compiled