from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, SimpleCookie, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from pymongo import MongoClient
import re
import json
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


def compiler_v4(req):
    compiled = [
        """<!doctype html><html lang="en"><head><!-- Required meta tags --><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no"></head><body>""",
        """<div>Hello World</div>""",
        """</body></html>"""]
    return "".join(compiled)