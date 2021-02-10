from django.http.response import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
import urllib.parse
from pymongo import MongoClient
import re
import os
import json
from django.template.defaultfilters import slugify
import linecache
import sys

client = MongoClient('mongodb://localhost:27017/')
db = client.acedbv2
coll_ra = db.agents_agent
coll_si = db.sites_site
coll_te = db.templates_template
coll_bl = db.blogs_blog


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print(f"""EXCEPTION IN ({filename}, LINE {lineno} "{line.strip()}"): {exc_obj}""")


def resource_page(request, site, page, **kwargs):
    mime_types = {
        '.css': 'text/css',
        '.csv': 'text/csv',
        '.html': 'text/html',
        '.js': 'text/javascript',
        '.json': 'application/json',
        '.jsonld': 'application/ld+json',
        '.php': 'application/x-httpd-php',
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

    compiled = f"""{page.content}"""
    return HttpResponse(compiled, content_type="text/plain")

def static_page(request, site, page, **kwargs):
    rep_codes = {
        'XXsitemetasXX': f"{site.sitemetas}",
        'XXpagemetasXX': f"{page.pagemetas}",
        'XXsitelinksXX': f"{site.sitelinks}",
        'XXpagelinksXX': f"{page.pagelinks}",
        'XXsitestyleXX': f"{site.sitestyle}",
        'XXtitleXX': f"{page.title}",
        'XXsiteheaderXX': f"{site.siteheader}",
        'XXcontentXX': f"{page.content}",
        'XXsitefooterXX': f"{site.sitefooter}",
        'XXsitescriptsXX': f"{site.sitescripts}",
        'XXpagescriptsXX': f"{page.pagescripts}",
        
    }
    compiled = f"""<!DOCTYPE html>
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

    for k, v in rep_codes.items():
        compiled = re.sub(k, v, compiled)
    return HttpResponse(compiled, content_type='text/html')

def individual_agent(request, site, pagename, **kwargs):
    compiled = "individual agent"
    return HttpResponse(compiled, content_type='text/plain')

def agents_by_location(request, site, pagename, **kwargs):
    compiled = "agents by location"
    return HttpResponse(compiled, content_type='text/plain')

def agents_by_corp(request, site, pagename, **kwargs):
    compiled = "agents by corp"
    return HttpResponse(compiled, content_type='text/plain')

def agents_query(request, site, pagename, **kwargs):
    compiled = "agents query"
    return HttpResponse(compiled, content_type='text/plain')

def sitemap_generator(request, **kwargs):
    return "sitemap generator"


