from django.urls import path
from django.http.response import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
import urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from .models import Agent
from .forms import AgentModelForm
from sites.models import Site
from templates.models import Template
from django.views.generic import UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
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


test_doc = """<!DOCTYPE html>
    <html lang="en">
    <head>
        <title>XXroutetitleXX</title>
    </head>
    <body>
        XXtestcontentXX
    </body>
    </html>"""



def abs_main(request, *args, **kwargs):
    site = get_object_or_404(Site, id=kwargs['siteid'])
    page = None
    compiled = "<div>"
    pagename = "/agents-by-state"
    for i in site.pages:
        if i.route == pagename:
            page = i
            break
    if page == None:
        return HttpResponse("", content_type='text/plain')
    else:
        rep_args = dict()
        url_args = dict()
        for k, v in kwargs.items():
            if type(v) == str:
                rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                url_args[k] = re.sub('_', ' ', v)
        u_key = "state"
        location_table = []
        loc_objs = list(coll_ra.find({}, {'_id': 0}).distinct(u_key))
        for i in loc_objs:
            u_val = re.sub(' ', '_', i)
            rel_link = urllib.parse.quote(f"/agents-by-state/{u_val}/")
            location_table.append([rel_link, i])
        compiled += f"""
        <p>{site.sitename}</p>
        <p>{page.route}</p>
        <p>{kwargs}</p>
        <p>{rep_args}</p>
        <p>{url_args}</p>
        <p>{location_table}</p>
        """
        compiled += "</div>"
        res = f"{test_doc}"
        res = re.sub('XXtestcontentXX', compiled, res)
        res = re.sub('XXroutetitleXX', pagename, res)
        return HttpResponse(res, content_type='text/html')


def abs_state(request, *args, **kwargs):
    site = get_object_or_404(Site, id=kwargs['siteid'])
    page = None
    compiled = "<div>"
    pagename = "/agents-by-state/state"
    for i in site.pages:
        if i.route == pagename:
            page = i
            break
    if page == None:
        return HttpResponse("", content_type='text/plain')
    else:
        rep_args = dict()
        url_args = dict()
        for k, v in kwargs.items():
            if type(v) == str:
                rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                url_args[k] = re.sub('_', ' ', v)
        agents_objs = list(coll_ra.find(url_args, {'_id': 0}))
        agent_table = []
        for i in agents_objs:
            agent = re.sub(' ', '_', i['agent'])
            state = re.sub(' ', '_', i['state'])
            county = re.sub(' ', '_', i['county'])
            city = re.sub(' ', '_', i['city'])
            rel_link = urllib.parse.quote(f"/registered-agents/{agent}-{state}-{county}-{city}/{i['id']}/")
            agent_table.append([rel_link, agent, f"{i['city']}, {i['state']}"])

        u_key = "city"
        location_table = []
        loc_objs = list(coll_ra.find(url_args, {'_id': 0}).distinct(u_key))
        for i in loc_objs:
            u_val = re.sub(' ', '_', i)
            rel_link = urllib.parse.quote(f"/agents-by-state/{kwargs['state']}/{u_val}/")
            location_table.append([rel_link, i])
        compiled += f"""
        <p>{site.sitename}</p>
        <p>{page.route}</p>
        <p>{kwargs}</p>
        <p>{rep_args}</p>
        <p>{url_args}</p>
        <p>{agent_table}</p>
        <p>{location_table}</p>
        """
        compiled += "</div>"

        res = f"{test_doc}"
        res = re.sub('XXtestcontentXX', compiled, res)
        res = re.sub('XXroutetitleXX', pagename, res)
        return HttpResponse(res, content_type='text/html')


def abs_city(request, *args, **kwargs):
    site = get_object_or_404(Site, id=kwargs['siteid'])
    page = None
    compiled = "<div>"
    pagename = "/agents-by-state/state/city"
    for i in site.pages:
        if i.route == pagename:
            page = i
            break
    if page == None:
        return HttpResponse("", content_type='text/plain')
    else:
        rep_args = dict()
        url_args = dict()
        for k, v in kwargs.items():
            if type(v) == str:
                rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                url_args[k] = re.sub('_', ' ', v)
        agents_objs = list(coll_ra.find(url_args, {'_id': 0}))
        agent_table = []
        for i in agents_objs:
            agent = re.sub(' ', '_', i['agent'])
            state = re.sub(' ', '_', i['state'])
            county = re.sub(' ', '_', i['county'])
            city = re.sub(' ', '_', i['city'])
            rel_link = urllib.parse.quote(f"/registered-agents/{agent}-{state}-{county}-{city}/{i['id']}/")
            agent_table.append([rel_link, agent, f"{i['city']}, {i['state']}"])

        compiled += f"""
        <p>{site.sitename}</p>
        <p>{page.route}</p>
        <p>{kwargs}</p>
        <p>{rep_args}</p>
        <p>{url_args}</p>
        <p>{agent_table}</p>
        """
        compiled += "</div>"

        res = f"{test_doc}"
        res = re.sub('XXtestcontentXX', compiled, res)
        res = re.sub('XXroutetitleXX', pagename, res)
        return HttpResponse(res, content_type='text/html')


def ps_agent(request, *args, **kwargs):
    site = get_object_or_404(Site, id=kwargs['siteid'])
    page = None
    compiled = "<div>"
    pagename = "/process-server/id"
    for i in site.pages:
        if i.route == pagename:
            page = i
            break
    if page == None:
        return HttpResponse("", content_type='text/plain')
    else:
        rep_args = dict()
        url_args = dict()
        for k, v in kwargs.items():
            if type(v) == str:
                rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                url_args[k] = re.sub('_', ' ', v)
        agents_objs = list(coll_ra.find(url_args, {'_id': 0}))
        agent_table = []
        for i in agents_objs:
            agent = re.sub(' ', '_', i['agent'])
            state = re.sub(' ', '_', i['state'])
            county = re.sub(' ', '_', i['county'])
            city = re.sub(' ', '_', i['city'])
            rel_link = urllib.parse.quote(f"/registered-agents/{agent}-{state}-{county}-{city}/{i['id']}/")
            agent_table.append([rel_link, agent, f"{i['city']}, {i['state']}"])

        u_key = "state"
        location_table = []
        loc_objs = list(coll_ra.find(url_args, {'_id': 0}).distinct(u_key))
        for i in loc_objs:
            u_val = re.sub(' ', '_', i)
            rel_link = urllib.parse.quote(f"/process-server/{kwargs['agent']}/{u_val}/")
            location_table.append([rel_link, i])
        compiled += f"""
        <p>{site.sitename}</p>
        <p>{page.route}</p>
        <p>{kwargs}</p>
        <p>{rep_args}</p>
        <p>{url_args}</p>
        <p>{agent_table}</p>
        <p>{location_table}</p>
        """
        compiled += "</div>"

        res = f"{test_doc}"
        res = re.sub('XXtestcontentXX', compiled, res)
        res = re.sub('XXroutetitleXX', pagename, res)
        return HttpResponse(res, content_type='text/html')


def ps_state(request, *args, **kwargs):
    site = get_object_or_404(Site, id=kwargs['siteid'])
    page = None
    compiled = "<div>"
    pagename = "/process-server/id/state"
    for i in site.pages:
        if i.route == pagename:
            page = i
            break
    if page == None:
        return HttpResponse("", content_type='text/plain')
    else:
        rep_args = dict()
        url_args = dict()
        for k, v in kwargs.items():
            if type(v) == str:
                rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                url_args[k] = re.sub('_', ' ', v)
        agents_objs = list(coll_ra.find(url_args, {'_id': 0}))
        agent_table = []
        for i in agents_objs:
            agent = re.sub(' ', '_', i['agent'])
            state = re.sub(' ', '_', i['state'])
            county = re.sub(' ', '_', i['county'])
            city = re.sub(' ', '_', i['city'])
            rel_link = urllib.parse.quote(f"/registered-agents/{agent}-{state}-{county}-{city}/{i['id']}/")
            agent_table.append([rel_link, agent, f"{i['city']}, {i['state']}"])

        u_key = "city"
        location_table = []
        loc_objs = list(coll_ra.find(url_args, {'_id': 0}).distinct(u_key))
        for i in loc_objs:
            u_val = re.sub(' ', '_', i)
            rel_link = urllib.parse.quote(f"/process-server/{kwargs['agent']}/{kwargs['state']}/{u_val}/")
            location_table.append([rel_link, i])
        compiled += f"""
        <p>{site.sitename}</p>
        <p>{page.route}</p>
        <p>{kwargs}</p>
        <p>{rep_args}</p>
        <p>{url_args}</p>
        <p>{agent_table}</p>
        <p>{location_table}</p>
        """
        compiled += "</div>"

        res = f"{test_doc}"
        res = re.sub('XXtestcontentXX', compiled, res)
        res = re.sub('XXroutetitleXX', pagename, res)
        return HttpResponse(res, content_type='text/html')


def ps_city(request, *args, **kwargs):
    site = get_object_or_404(Site, id=kwargs['siteid'])
    page = None
    compiled = "<div>"
    pagename = "/process-server/id/state/city"
    for i in site.pages:
        if i.route == pagename:
            page = i
            break
    if page == None:
        return HttpResponse("", content_type='text/plain')
    else:
        rep_args = dict()
        url_args = dict()
        for k, v in kwargs.items():
            if type(v) == str:
                rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                url_args[k] = re.sub('_', ' ', v)
        agents_objs = list(coll_ra.find(url_args, {'_id': 0}))
        agent_table = []
        for i in agents_objs:
            agent = re.sub(' ', '_', i['agent'])
            state = re.sub(' ', '_', i['state'])
            county = re.sub(' ', '_', i['county'])
            city = re.sub(' ', '_', i['city'])
            rel_link = urllib.parse.quote(f"/registered-agents/{agent}-{state}-{county}-{city}/{i['id']}/")
            agent_table.append([rel_link, agent, f"{i['city']}, {i['state']}"])
        compiled += f"""
        <p>{site.sitename}</p>
        <p>{page.route}</p>
        <p>{kwargs}</p>
        <p>{rep_args}</p>
        <p>{url_args}</p>
        <p>{agent_table}</p>
        """
        compiled += "</div>"

        res = f"{test_doc}"
        res = re.sub('XXtestcontentXX', compiled, res)
        res = re.sub('XXroutetitleXX', pagename, res)
        return HttpResponse(res, content_type='text/html')



def ra_search(request, *args, **kwargs):
    site = get_object_or_404(Site, id=kwargs['siteid'])
    page = None
    compiled = "<div>"
    pagename = "/registered-agents/search/key/value"
    for i in site.pages:
        if i.route == pagename:
            page = i
            break
    if page == None:
        return HttpResponse("", content_type='text/plain')
    else:
        rep_args = dict()
        url_args = dict()
        for k, v in kwargs.items():
            if type(v) == str:
                rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                url_args[k] = re.sub('_', ' ', v)
        agents_objs = list(coll_ra.find({"$text":{"$search":url_args['query']}},{"score":{"$meta":"textScore"}}).sort([("score",{"$meta":"textScore"})]))
        agent_table = []
        for i in agents_objs:
            agent = re.sub(' ', '_', i['agent'])
            state = re.sub(' ', '_', i['state'])
            county = re.sub(' ', '_', i['county'])
            city = re.sub(' ', '_', i['city'])
            rel_link = urllib.parse.quote(f"/registered-agents/{agent}-{state}-{county}-{city}/{i['id']}/")
            agent_table.append([rel_link, agent, f"{i['city']}, {i['state']}"])

        compiled += f"""
        <p>{site.sitename}</p>
        <p>{page.route}</p>
        <p>{kwargs}</p>
        <p>{rep_args}</p>
        <p>{url_args}</p>
        <p>{agent_table}</p>
        """
        compiled += "</div>"

        res = f"{test_doc}"
        res = re.sub('XXtestcontentXX', compiled, res)
        res = re.sub('XXroutetitleXX', pagename, res)
        return HttpResponse(res, content_type='text/html')


def ra_agent(request, *args, **kwargs):
    site = get_object_or_404(Site, id=kwargs['siteid'])
    page = None
    compiled = "<div>"
    pagename = "/registered-agents/id"
    for i in site.pages:
        if i.route == pagename:
            page = i
            break
    if page == None:
        return HttpResponse("", content_type='text/plain')
    else:
        rep_args = dict()
        url_args = dict()
        for k, v in kwargs.items():
            if type(v) == str:
                rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                url_args[k] = re.sub('_', ' ', v)
        agents_objs = list(coll_ra.find({'id': kwargs['agentid']}, {'_id': 0}))

        compiled += f"""
        <p>{site.sitename}</p>
        <p>{page.route}</p>
        <p>{kwargs}</p>
        <p>{rep_args}</p>
        <p>{url_args}</p>
        <p>{agents_objs}</p>
        """
        compiled += "</div>"

        return HttpResponse(compiled, content_type='text/html')



urlpatterns = [
    #path('compile/<int:siteid>/', get_home),
    #path('compile/<int:siteid>/blog/posts/', bl_all),
    #path('compile/<int:siteid>/blog/posts/<str:blogtitle>-<int:agentid>/', bl_post),
    path('test/<int:siteid>/agents-by-state/', abs_main),
    path('test/<int:siteid>/agents-by-state/<str:state>/', abs_state),
    path('test/<int:siteid>/agents-by-state/<str:state>/<str:city>/', abs_city),
    path('test/<int:siteid>/process-server/<str:agent>/', ps_agent),
    path('test/<int:siteid>/process-server/<str:agent>/<str:state>/', ps_state),
    path('test/<int:siteid>/process-server/<str:agent>/<str:state>/<str:city>/', ps_city),
    path('test/<int:siteid>/registered-agents/search/<str:query>/', ra_search),
    path('test/<int:siteid>/registered-agents/<str:agent>-<str:state>-<str:county>-<str:city>/<int:agentid>/', ra_agent),
    #path('compile/<int:siteid>/<str:page>/', compilerv5, name='agent-page-view'),
]

