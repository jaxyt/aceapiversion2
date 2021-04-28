from django.http.response import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
import urllib.parse
from pymongo import MongoClient
import re
import os
import json
from django.template.defaultfilters import slugify
import linecache
import sys
from datetime import date

client = MongoClient('mongodb://localhost:27017/')
db = client.acedbv2
coll_ra = db.agents_agent
coll_si = db.sites_site
coll_te = db.templates_template
coll_bl = db.blogs_blog

basic_doc = """<!DOCTYPE html>
    <html lang="en">
    <head>
        XXsitemetasXX
        XXpagemetasXX
        XXsitelinksXX
        XXpagelinksXX
        XXsitestyleXX
        <title>XXtitleXX</title>
    </head>
    <body>
        XXsiteheaderXX
        XXcontentXX
        XXsitefooterXX
        XXsitescriptsXX
        XXpagescriptsXX
    </body>
    </html>"""

admin_doc = """<!DOCTYPE html>
    <html lang="en">
    <head>
        XXsitemetasXX
        XXpagemetasXX
        XXsitelinksXX
        XXpagelinksXX
        XXsitestyleXX
        <title>XXtitleXX</title>
    </head>
    <body>
        <!--##START siteheader START##-->
        XXsiteheaderXX
        <!--##END siteheader END##-->
        <!--##START content START##-->
        XXcontentXX
        <!--##END content END##-->
        <!--##START sitefooter START##-->
        XXsitefooterXX
        <!--##END sitefooter END##-->
        XXsitescriptsXX
        XXpagescriptsXX
        <div id="metas-and-style" style="display: none;">
            <textarea name="" id="pagemetas-form">XXpagemetasXX</textarea>
            <textarea name="" id="sitestyle-form">XXsitestyleXX</textarea>
        </div>
        <div id="hidden-form-attrs" style="display: none;">
            <textarea name="" id="siteid-form">XXsiteidXX</textarea>
            <textarea name="" id="pageroute-form">XXpagerouteXX</textarea>
        </div>
    </body>
    </html>"""


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print(f"""{exc_type} EXCEPTION IN ({filename}, LINE {lineno} "{line.strip()}"): {exc_obj}""")

def replace_shortcodes(site, compiled):
    temp = list(coll_te.find({'id': site.id}, {'_id': 0}))[0]
    s = list(coll_si.find({'id': site.id}, {'_id': 0}))[0]
    for i in site.shortcodes:
        compiled = re.sub(f"XX{i.name}XX", f"{i.value}", compiled)
    for i in temp['shortcodes']:
        compiled = re.sub(f"XX{i['name']}XX", f"{i['value']}", compiled)
    for k, v in s.items():
        if type(v) is str:
            compiled = re.sub(f"XX{k}XX", f"{v}", compiled)
    html_sitemap = """<div><ul class="sitemap-links">"""
    for i in s['pages']:
        if re.search(r'(^/locations)|(^/registered-agents)|(^/telecom-agents)|(^/process-server)|(/blog/posts/id)|(/blog/posts)|(/html-sitemap)|(^/agents-by-state/)|(\.)', i['route']) is None:
                if i['route'] == "/":
                    html_sitemap += """<li><a href="/">Home</a></li>"""
                else:
                    html_sitemap += f"""<li><a href="{i['route']}">{i['title'] if i['title'] else " ".join(i['route'].split("/")).title()}</a></li>"""
    html_sitemap += """</ul></div>"""
    compiled = re.sub('XXsitemapXX', html_sitemap, compiled)
    copyright_content = f"""Copyright © 1997 - {date.today().year}. Inspired by <a href="https://www.goshgo.com">GoshGo, Motivated by Perfection.</a>"""
    compiled = re.sub('XXcopyrightXX', copyright_content, compiled)
    compiled = re.sub(r'XX\w+XX', '', compiled)
    return compiled


def resource_page(request, site, pagedoc, **kwargs):
    mime_types = {
        '.css': 'text/css',
        '.csv': 'text/csv',
        '.html': 'text/html',
        '.js': 'text/javascript',
        '.json': 'application/json',
        '.jsonld': 'application/ld+json',
        '.php': 'application/x-httpd-php',
        '.ppp': 'application/x-httpd-php',
        '.pdf': 'application/pdf',
        '.jpeg': 'image/jpeg',
        '.ico': 'image/vnd.microsoft.icon',
        '.png': 'image/png',
        '.svg': 'image/svg+xml',
        '.sh': 'application/x-sh',
        '.xml': 'application/xml',
        '.zip': 'application/zip',
        '.7z': 'application/x-7z-compressed',
        '.gz': 'application/gzip',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }

    mime_type = "text/plain"
    for k, v in mime_types.items():
        regx = re.compile(f"{k}$")
        m = re.search(regx, kwargs['page'])
        if m is not None:
            mime_type = v
            break

    compiled = f"""{pagedoc.content}"""
    compiled = replace_shortcodes(site, compiled)
    return HttpResponse(compiled, content_type=mime_type)


def sitemap_generator(request, site):
    states = list(coll_ra.find().distinct('state'))
    agents = list(coll_ra.find().distinct('agent'))
    pages = [i.route for i in site.pages if re.search(re.compile("^/((registered-agents)|(process-server)|(agents-by-state)|([\w-]+\.\w{2,4}))"), f"{i.route}") is None]
    process_server_urls = []
    registered_agent_urls = []
    agents_by_state_urls = []
    page_urls = []
    xml_urls = []
    #print(agents)

    for i in agents:
        process_server_urls.append(f'\n\t<url>\n\t\t<loc>https://www.{site.sitename}.com'+urllib.parse.quote(re.sub(' ', '_', f"""/process-server/{i}/"""))+"</loc>\n\t</url>")
        a_states = list(coll_ra.find({"agent": i}).distinct("state"))
        #print(a_states)
        for n in a_states:
            process_server_urls.append(f'\n\t<url>\n\t\t<loc>https://www.{site.sitename}.com'+urllib.parse.quote(re.sub(' ', '_', f"""/process-server/{i}/{n}/"""))+"</loc>\n\t</url>")
            a_cities = list(coll_ra.find({"agent": i, 'state': n}).distinct("city"))
            #print(a_cities)
            for k in a_cities:
                process_server_urls.append(f'\n\t<url>\n\t\t<loc>https://www.{site.sitename}.com'+urllib.parse.quote(re.sub(' ', '_', f"""/process-server/{i}/{n}/{k}/"""))+"</loc>\n\t</url>")
    process_server_urls.sort()
    process_server_urls.sort(key=len, reverse=True)

    for n in states:
        agents_by_state_urls.append(f'\n\t<url>\n\t\t<loc>https://www.{site.sitename}.com'+urllib.parse.quote(re.sub(' ', '_', f"""/agents-by-state/{n}/"""))+"</loc>\n\t</url>")
        s_cities = list(coll_ra.find({'state': n}).distinct("city"))
        #print(s_cities)
        for k in s_cities:
            agents_by_state_urls.append(f'\n\t<url>\n\t\t<loc>https://www.{site.sitename}.com'+urllib.parse.quote(re.sub(' ', '_', f"""/agents-by-state/{n}/{k}/"""))+"</loc>\n\t</url>")
    agents_by_state_urls.sort()
    agents_by_state_urls.sort(key=len, reverse=True)

    for i in list(coll_ra.find({}, {'_id': 0})):
        registered_agent_urls.append(f'\n\t<url>\n\t\t<loc>https://www.{site.sitename}.com'+urllib.parse.quote(re.sub(' ', '_', f"""/registered-agents/{i['agent']}--{i['state']}--{i['county']}--{i['city']}/{i['id']}/"""))+"</loc>\n\t</url>")
    registered_agent_urls.sort()
    registered_agent_urls.sort(key=len, reverse=True)

    for i in pages:
        page_urls.append(f'\n\t<url>\n\t\t<loc>https://www.{site.sitename}.com'+urllib.parse.quote(f"""{i}/""")+"</loc>\n\t</url>")

    print(len(page_urls))
    print(len(registered_agent_urls))
    print(len(process_server_urls))
    print(len(agents_by_state_urls))
    print(len(page_urls)+len(registered_agent_urls)+len(process_server_urls)+len(agents_by_state_urls))
    xml_urls = ''.join(page_urls) + ''.join(registered_agent_urls) + ''.join(process_server_urls) + ''.join(agents_by_state_urls)
    
    xml_doc = """<?xml version="1.0" encoding="utf-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">""" + xml_urls + """\n</urlset>"""
    return HttpResponse(xml_doc, content_type="application/xml") 


