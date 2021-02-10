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


def static_page(request, *args, **kwargs):
    return "static page"

def individual_agent(request, *args, **kwargs):
    return "individual agent"

def agents_by_location(request, *args, **kwargs):
    return "agents by location"

def agents_by_corp(request, *args, **kwargs):
    return "agents by corp"

def agents_query(request, *args, **kwargs):
    return "agents query"

def sitemap_generator(request, *args, **kwargs):
    return "sitemap generator"


