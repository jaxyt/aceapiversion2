from django.http.response import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.http import Http404
import urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from .models import Agent
from .forms import AgentModelForm
from sites.models import Site
from blogs.models import Blog
from templates.models import Template
from django.views.generic import UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
import os
import json
import re
import linecache
import sys
from datetime import date
from .functions import PrintException, sitemap_generator
from pymongo import MongoClient
# Create your views here.
module_dir = os.path.dirname(__file__)  # get current directory
file_path = os.path.join(module_dir, 'sop-to-mongo.json')

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


def replace_shortcodes(site, compiled):
    temp = list(coll_te.find({'id': site.id}, {'_id': 0}))[0]
    s = list(coll_si.find({'id': site.id}, {'_id': 0}))[0]
    for k, v in s.items():
        if type(v) is str:
            compiled = re.sub(f"XX{k}XX", f"{v}", compiled)
    for i in site.shortcodes:
        compiled = re.sub(f"XX{i.name}XX", f"{i.value}", compiled)
    for i in temp['shortcodes']:
        compiled = re.sub(f"XX{i['name']}XX", f"{i['value']}", compiled)
    copyright_content = f"""Copyright &copy; 1997 - {date.today().year}. Inspired by <a href="https://www.goshgo.com">GoshGo, Motivated by Perfection.</a>"""
    compiled = re.sub('XXcopyrightXX', copyright_content, compiled)    
    return compiled


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def home_view(request, *args, **kwargs):
    try:
        site = get_object_or_404(Site, id=int(kwargs['siteid']))
        page = None
        pagename = "/"
        for i in site.pages:
            if i.route == pagename:
                page = i
                break
        if page == None:
            return home_view(request, *args, **kwargs)
        else:
            rep_args = dict()
            url_args = dict()
            for k, v in kwargs.items():
                if type(v) == str:
                    rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                    url_args[k] = re.sub('_', ' ', v)
            res = f"{basic_doc}"
            rep_codes = {
                'XXpagemetasXX': f"{page.pagemetas}",
                'XXpagelinksXX': f"{page.pagelinks}",
                'XXtitleXX': f"{page.title}",
                'XXcontentXX': f"{page.content}",
                'XXpagescriptsXX': f"{page.pagescripts}",
            }
            for k, v in rep_codes.items():
                res = re.sub(k, v, res)
            for k, v in rep_args.items():
                res = re.sub(k, v, res)
            res = replace_shortcodes(site, res)
            res = re.sub(r'XX\w+XX', '', res)
            return HttpResponse(res, content_type='text/html')
    except Exception as e:
        print(e)
        PrintException()

def get_static_page(request, *args, **kwargs):
    try:
        site = get_object_or_404(Site, id=kwargs['siteid'])
        page = None
        pagename = f"/{kwargs['page']}"
        if re.search(r'^/sitemap\.xml$', pagename):
            return sitemap_generator(request, site)
        elif re.search(r'^/robots\.txt$', pagename):
            return HttpResponse(f"""User-agent: *\nDisallow: \nSitemap: https://www.{site.sitename}.com/sitemap.xml/""", content_type='text/plain')
        elif re.search(r'^/\w+\.\w{2,4}$', pagename):
            return get_resource_page(request, site, pagename, *args, **kwargs)
        else:
            for i in site.pages:
                if i.route == pagename:
                    page = i
                    break
            if page == None:
                return home_view(request, *args, **kwargs)
            else:
                rep_args = dict()
                url_args = dict()
                for k, v in kwargs.items():
                    if type(v) == str:
                        rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                        url_args[k] = re.sub('_', ' ', v)
                res = f"{basic_doc}"
                rep_codes = {
                    'XXpagemetasXX': f"{page.pagemetas}",
                    'XXpagelinksXX': f"{page.pagelinks}",
                    'XXtitleXX': f"{page.title}",
                    'XXcontentXX': f"{page.content}",
                    'XXpagescriptsXX': f"{page.pagescripts}",
                }
                for k, v in rep_codes.items():
                    res = re.sub(k, v, res)
                for k, v in rep_args.items():
                    res = re.sub(k, v, res)
                res = replace_shortcodes(site, res)
                res = re.sub(r'XX\w+XX', '', res)
                return HttpResponse(res, content_type='text/html')
    except Exception as e:
        print(e)
        PrintException()
        return home_view(request, *args, **kwargs)


def get_resource_page(request, site, pagename, *args, **kwargs):
    try:
        mime_type = 'text/plain'
        res = ""
        page = None
        for i in site.pages:
            if i.route == pagename:
                page = i
                break
        if page is None:
            return HttpResponse(res, content_type=mime_type)
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
        for k, v in mime_types.items():
            regx = re.compile(f"{k}$")
            m = re.search(regx, pagename)
            if m is not None:
                mime_type = v
                break
        res = f"{page.content}"
        res = replace_shortcodes(site, res)
        return HttpResponse(res, content_type=mime_type)
    except Exception as e:
        print(e)
        PrintException()
        return HttpResponse("", content_type='text/plain')


def abs_main(request, *args, **kwargs):
    try:
        site = get_object_or_404(Site, id=kwargs['siteid'])
        page = None
        pagename = "/agents-by-state"
        for i in site.pages:
            if i.route == pagename:
                page = i
                break
        if page == None:
            return home_view(request, *args, **kwargs)
        else:
            rep_args = dict()
            url_args = dict()
            for k, v in kwargs.items():
                if type(v) == str:
                    rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                    url_args[k] = re.sub('_', ' ', v)
            u_key = "state"
            location_table = """<div class="process-server-corp-state-links">"""
            loc_objs = list(coll_ra.find({}, {'_id': 0}).distinct(u_key))
            for i in loc_objs:
                u_val = re.sub(' ', '_', i)
                rel_link = urllib.parse.quote(f"/agents-by-state/{u_val}/")
                location_table += f"""<a href="{rel_link}">{i}</a>"""
            location_table += """</div>"""    
            res = f"{basic_doc}"
            rep_codes = {
                'XXpagemetasXX': f"{page.pagemetas}",
                'XXpagelinksXX': f"{page.pagelinks}",
                'XXtitleXX': f"{page.title}",
                'XXcontentXX': f"{page.content}",
                'XXpagescriptsXX': f"{page.pagescripts}",
            }
            for k, v in rep_codes.items():
                res = re.sub(k, v, res)
            res = re.sub('XXagentsbystateXX', location_table, res)
            for k, v in rep_args.items():
                res = re.sub(k, v, res)
            res = replace_shortcodes(site, res)
            res = re.sub(r'XX\w+XX', '', res)
            return HttpResponse(res, content_type='text/html')
    except Exception as e:
        print(e)
        PrintException()
        return home_view(request, *args, **kwargs)

def abs_state(request, *args, **kwargs):
    try:
        site = get_object_or_404(Site, id=kwargs['siteid'])
        page = None
        pagename = "/agents-by-state/state"
        for i in site.pages:
            if i.route == pagename:
                page = i
                break
        if page == None:
            return home_view(request, *args, **kwargs)
        else:
            rep_args = dict()
            url_args = dict()
            for k, v in kwargs.items():
                if type(v) == str:
                    rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                    url_args[k] = re.sub('_', ' ', v)
            agents_objs = list(coll_ra.find(url_args, {'_id': 0}))
            if len(agents_objs):
                agent_table = """
                <div class="table-responsive">
                    <table id="default_order" class="table table-striped table-bordered display" style="width:100%">
                        <thead>
                            <tr>
                                <th>Registered Agent</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                for i in agents_objs:
                    agent = re.sub(' ', '_', i['agent'])
                    state = re.sub(' ', '_', i['state'])
                    county = re.sub(' ', '_', i['county'])
                    city = re.sub(' ', '_', i['city'])
                    rel_link = urllib.parse.quote(f"/registered-agents/{agent}--{state}--{county}--{city}/{i['id']}/")
                    agent_table += f"""<tr><td><a href="{rel_link}">{i['agent']} - {i['city']}, {i['stateacronym']}</a></td></tr>"""
                agent_table += """
                        </tbody>
                    </table>
                </div>
                """

                u_key = "city"
                location_table = """<div class="process-server-corp-state-links">"""
                loc_objs = list(coll_ra.find(url_args, {'_id': 0}).distinct(u_key))
                for i in loc_objs:
                    u_val = re.sub(' ', '_', i)
                    rel_link = urllib.parse.quote(f"/agents-by-state/{kwargs['state']}/{u_val}/")
                    location_table += f"""<a href="{rel_link}">{i}</a>"""
                location_table += """</div>""" 
                res = f"{basic_doc}"
                rep_codes = {
                    'XXpagemetasXX': f"{page.pagemetas}",
                    'XXpagelinksXX': f"{page.pagelinks}",
                    'XXtitleXX': f"{page.title}",
                    'XXcontentXX': f"{page.content}",
                    'XXpagescriptsXX': f"{page.pagescripts}",
                }
                for k, v in rep_codes.items():
                    res = re.sub(k, v, res)
                res = re.sub('XXagentsXX', agent_table, res)
                res = re.sub('XXsublocationsXX', location_table, res)
                for k, v in rep_args.items():
                    res = re.sub(k, v, res)
                res = replace_shortcodes(site, res)
                res = re.sub(r'XX\w+XX', '', res)
                return HttpResponse(res, content_type='text/html')
            else:
                return home_view(request, *args, **kwargs)
                
    except Exception as e:
        print(e)
        PrintException()
        return home_view(request, *args, **kwargs)

def abs_city(request, *args, **kwargs):
    try:
        site = get_object_or_404(Site, id=kwargs['siteid'])
        page = None
        compiled = "<div>"
        pagename = "/agents-by-state/state/city"
        for i in site.pages:
            if i.route == pagename:
                page = i
                break
        if page == None:
            return home_view(request, *args, **kwargs)
        else:
            rep_args = dict()
            url_args = dict()
            for k, v in kwargs.items():
                if type(v) == str:
                    rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                    url_args[k] = re.sub('_', ' ', v)
            agents_objs = list(coll_ra.find(url_args, {'_id': 0}))
            if len(agents_objs):
                agent_table = """
                    <div class="table-responsive">
                        <table id="default_order" class="table table-striped table-bordered display" style="width:100%">
                            <thead>
                                <tr>
                                    <th>Registered Agent</th>
                                </tr>
                            </thead>
                            <tbody>
                    """
                for i in agents_objs:
                    agent = re.sub(' ', '_', i['agent'])
                    state = re.sub(' ', '_', i['state'])
                    county = re.sub(' ', '_', i['county'])
                    city = re.sub(' ', '_', i['city'])
                    rel_link = urllib.parse.quote(f"/registered-agents/{agent}--{state}--{county}--{city}/{i['id']}/")
                    agent_table += f"""<tr><td><a href="{rel_link}">{i['agent']} - {i['city']}, {i['stateacronym']}</a></td></tr>"""
                agent_table += """
                            </tbody>
                        </table>
                    </div>
                    """
                res = f"{basic_doc}"
                rep_codes = {
                    'XXpagemetasXX': f"{page.pagemetas}",
                    'XXpagelinksXX': f"{page.pagelinks}",
                    'XXtitleXX': f"{page.title}",
                    'XXcontentXX': f"{page.content}",
                    'XXpagescriptsXX': f"{page.pagescripts}",
                }
                for k, v in rep_codes.items():
                    res = re.sub(k, v, res)
                res = re.sub('XXagentsXX', agent_table, res)
                for k, v in rep_args.items():
                    res = re.sub(k, v, res)
                res = replace_shortcodes(site, res)
                res = re.sub(r'XX\w+XX', '', res)
                return HttpResponse(res, content_type='text/html')
            else:
                return home_view(request, *args, **kwargs)
            
    except Exception as e:
        print(e)
        PrintException()
        return home_view(request, *args, **kwargs)

def ps_agent(request, *args, **kwargs):
    try:
        site = get_object_or_404(Site, id=kwargs['siteid'])
        page = None
        compiled = "<div>"
        pagename = "/process-server/id"
        for i in site.pages:
            if i.route == pagename:
                page = i
                break
        if page == None:
            return home_view(request, *args, **kwargs)
        else:
            rep_args = dict()
            url_args = dict()
            for k, v in kwargs.items():
                if type(v) == str:
                    rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                    url_args[k] = re.sub('_', ' ', v)
            agents_objs = list(coll_ra.find(url_args, {'_id': 0}))
            if len(agents_objs):
                agent_table = """
                    <div class="table-responsive">
                        <table id="default_order" class="table table-striped table-bordered display" style="width:100%">
                            <thead>
                                <tr>
                                    <th>Registered Agent</th>
                                </tr>
                            </thead>
                            <tbody>
                    """
                for i in agents_objs:
                    agent = re.sub(' ', '_', i['agent'])
                    state = re.sub(' ', '_', i['state'])
                    county = re.sub(' ', '_', i['county'])
                    city = re.sub(' ', '_', i['city'])
                    rel_link = urllib.parse.quote(f"/registered-agents/{agent}--{state}--{county}--{city}/{i['id']}/")
                    agent_table += f"""<tr><td><a href="{rel_link}">{i['agent']} - {i['city']}, {i['stateacronym']}</a></td></tr>"""
                agent_table += """
                            </tbody>
                        </table>
                    </div>
                    """
                u_key = "state"
                location_table = """<div class="process-server-corp-state-links">"""
                loc_objs = list(coll_ra.find(url_args, {'_id': 0}).distinct(u_key))
                for i in loc_objs:
                    u_val = re.sub(' ', '_', i)
                    rel_link = urllib.parse.quote(f"/process-server/{kwargs['agent']}/{u_val}/")
                    location_table += f"""<a href="{rel_link}">{i}</a>"""
                location_table += """</div>""" 

                res = f"{basic_doc}"
                rep_codes = {
                    'XXpagemetasXX': f"{page.pagemetas}",
                    'XXpagelinksXX': f"{page.pagelinks}",
                    'XXtitleXX': f"{page.title}",
                    'XXcontentXX': f"{page.content}",
                    'XXpagescriptsXX': f"{page.pagescripts}",
                }
                for k, v in rep_codes.items():
                    res = re.sub(k, v, res)
                res = re.sub('XXagentsXX', agent_table, res)
                res = re.sub('XXsublocationsXX', location_table, res)
                for k, v in rep_args.items():
                    res = re.sub(k, v, res)
                res = replace_shortcodes(site, res)
                res = re.sub(r'XX\w+XX', '', res)
                return HttpResponse(res, content_type='text/html')
            else:
                return home_view(request, *args, **kwargs)
    except Exception as e:
        print(e)
        PrintException()
        return home_view(request, *args, **kwargs)

def ps_state(request, *args, **kwargs):
    try:
        site = get_object_or_404(Site, id=kwargs['siteid'])
        page = None
        compiled = "<div>"
        pagename = "/process-server/id/state"
        for i in site.pages:
            if i.route == pagename:
                page = i
                break
        if page == None:
            return home_view(request, *args, **kwargs)
        else:
            rep_args = dict()
            url_args = dict()
            for k, v in kwargs.items():
                if type(v) == str:
                    rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                    url_args[k] = re.sub('_', ' ', v)
            agents_objs = list(coll_ra.find(url_args, {'_id': 0}))
            if len(agents_objs):
                agent_table = """
                    <div class="table-responsive">
                        <table id="default_order" class="table table-striped table-bordered display" style="width:100%">
                            <thead>
                                <tr>
                                    <th>Registered Agent</th>
                                </tr>
                            </thead>
                            <tbody>
                    """
                for i in agents_objs:
                    agent = re.sub(' ', '_', i['agent'])
                    state = re.sub(' ', '_', i['state'])
                    county = re.sub(' ', '_', i['county'])
                    city = re.sub(' ', '_', i['city'])
                    rel_link = urllib.parse.quote(f"/registered-agents/{agent}--{state}--{county}--{city}/{i['id']}/")
                    agent_table += f"""<tr><td><a href="{rel_link}">{i['agent']} - {i['city']}, {i['stateacronym']}</a></td></tr>"""
                agent_table += """
                            </tbody>
                        </table>
                    </div>
                    """

                u_key = "city"
                location_table = """<div class="process-server-corp-state-links">"""
                loc_objs = list(coll_ra.find(url_args, {'_id': 0}).distinct(u_key))
                for i in loc_objs:
                    u_val = re.sub(' ', '_', i)
                    rel_link = urllib.parse.quote(f"/process-server/{kwargs['agent']}/{kwargs['state']}/{u_val}/")
                    location_table += f"""<a href="{rel_link}">{i}</a>"""
                location_table += """</div>""" 
                res = f"{basic_doc}"
                rep_codes = {
                    'XXpagemetasXX': f"{page.pagemetas}",
                    'XXpagelinksXX': f"{page.pagelinks}",
                    'XXtitleXX': f"{page.title}",
                    'XXcontentXX': f"{page.content}",
                    'XXpagescriptsXX': f"{page.pagescripts}",
                }
                for k, v in rep_codes.items():
                    res = re.sub(k, v, res)
                res = re.sub('XXagentsXX', agent_table, res)
                res = re.sub('XXsublocationsXX', location_table, res)
                for k, v in rep_args.items():
                    res = re.sub(k, v, res)
                res = replace_shortcodes(site, res)
                res = re.sub(r'XX\w+XX', '', res)
                return HttpResponse(res, content_type='text/html')
            else:
                return home_view(request, *args, **kwargs)
            
    except Exception as e:
        print(e)
        PrintException()
        return home_view(request, *args, **kwargs)

def ps_city(request, *args, **kwargs):
    try:
        site = get_object_or_404(Site, id=kwargs['siteid'])
        page = None
        compiled = "<div>"
        pagename = "/process-server/id/state/city"
        for i in site.pages:
            if i.route == pagename:
                page = i
                break
        if page == None:
            return home_view(request, *args, **kwargs)
        else:
            rep_args = dict()
            url_args = dict()
            for k, v in kwargs.items():
                if type(v) == str:
                    rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                    url_args[k] = re.sub('_', ' ', v)
            agents_objs = list(coll_ra.find(url_args, {'_id': 0}))
            if len(agents_objs):
                agent_table = """
                    <div class="table-responsive">
                        <table id="default_order" class="table table-striped table-bordered display" style="width:100%">
                            <thead>
                                <tr>
                                    <th>Registered Agent</th>
                                </tr>
                            </thead>
                            <tbody>
                    """
                for i in agents_objs:
                    agent = re.sub(' ', '_', i['agent'])
                    state = re.sub(' ', '_', i['state'])
                    county = re.sub(' ', '_', i['county'])
                    city = re.sub(' ', '_', i['city'])
                    rel_link = urllib.parse.quote(f"/registered-agents/{agent}--{state}--{county}--{city}/{i['id']}/")
                    agent_table += f"""<tr><td><a href="{rel_link}">{i['agent']} - {i['city']}, {i['stateacronym']}</a></td></tr>"""
                agent_table += """
                        </tbody>
                    </table>
                </div>
                """

                res = f"{basic_doc}"
                rep_codes = {
                    'XXpagemetasXX': f"{page.pagemetas}",
                    'XXpagelinksXX': f"{page.pagelinks}",
                    'XXtitleXX': f"{page.title}",
                    'XXcontentXX': f"{page.content}",
                    'XXpagescriptsXX': f"{page.pagescripts}",
                }
                for k, v in rep_codes.items():
                    res = re.sub(k, v, res)
                res = re.sub('XXagentsXX', agent_table, res)
                for k, v in rep_args.items():
                    res = re.sub(k, v, res)
                res = replace_shortcodes(site, res)
                res = re.sub(r'XX\w+XX', '', res)
                return HttpResponse(res, content_type='text/html')
            else:
                return home_view(request, *args, **kwargs)
            
    except Exception as e:
        print(e)
        PrintException()
        return home_view(request, *args, **kwargs)


def blog_main(request, *args, **kwargs):
    try:
        site = get_object_or_404(Site, id=kwargs['siteid'])
        page = None
        pagename = "/blog/posts"
        for i in site.pages:
            if i.route == pagename:
                page = i
                break
        if page == None:
            return home_view(request, *args, **kwargs)
        else:
            rep_args = dict()
            url_args = dict()
            for k, v in kwargs.items():
                if type(v) == str:
                    rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                    url_args[k] = re.sub('_', ' ', v)
            blog_objs = list(coll_bl.find({'blogcategory': site.blogcategory}, {'_id': 0}))
            blog_table = """
            <div class="snippets">
            """
            for i in blog_objs:
                post_title = re.sub(' ', '_', i['blogtitle'])
                state = re.sub(' ', '_', i['state'])
                county = re.sub(' ', '_', i['county'])
                city = re.sub(' ', '_', i['city'])
                rel_link = urllib.parse.quote(f"/blog/posts/{post_title}-{i['id']}/")
                blog_table += f"""<div class="snippet"><h3><a href="{rel_link}">{i['agent']} - {i['city']}, {i['stateacronym']}</a></h3></div>"""
            blog_table += """
            </div>
            """
            res = f"{basic_doc}"
            rep_codes = {
                'XXpagemetasXX': f"{page.pagemetas}",
                'XXpagelinksXX': f"{page.pagelinks}",
                'XXtitleXX': f"{page.title}",
                'XXcontentXX': f"{page.content}",
                'XXpagescriptsXX': f"{page.pagescripts}",
            }
            for k, v in rep_codes.items():
                res = re.sub(k, v, res)
            res = re.sub('XXblogsnippetsXX', blog_table, res)
            for k, v in rep_args.items():
                res = re.sub(k, v, res)
            res = replace_shortcodes(site, res)
            res = re.sub(r'XX\w+XX', '', res)
            return HttpResponse(res, content_type='text/html')
    except Exception as e:
        print(e)
        PrintException()
        return home_view(request, *args, **kwargs)


def blog_post(request, *args, **kwargs):
    try:
        site = get_object_or_404(Site, id=kwargs['siteid'])
        page = None
        compiled = "<div>"
        pagename = "/blog/posts/id"
        for i in site.pages:
            if i.route == pagename:
                page = i
                break
        if page == None:
            return home_view(request, *args, **kwargs)
        else:
            rep_args = dict()
            url_args = dict()
            for k, v in kwargs.items():
                if type(v) == str:
                    rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                    url_args[k] = re.sub('_', ' ', v)
            b_check = get_object_or_404(Blog, id=kwargs['blogid'])
            blog_objs = list(coll_ra.find({'id': kwargs['blogid']}, {'_id': 0}))[0]

            res = f"{basic_doc}"
            rep_codes = {
                'XXpagemetasXX': f"{page.pagemetas}",
                'XXpagelinksXX': f"{page.pagelinks}",
                'XXtitleXX': f"{page.title}",
                'XXcontentXX': f"{page.content}",
                'XXpagescriptsXX': f"{page.pagescripts}",
            }
            for k, v in rep_codes.items():
                res = re.sub(k, v, res)
            for k, v in blog_objs.items():
                res = re.sub(f"XX{k}XX", f"{v}", res)
            res = replace_shortcodes(site, res)
            res = re.sub(r'XX\w+XX', '', res)
            return HttpResponse(res, content_type='text/html')
    except Exception as e:
        print(e)
        PrintException()
        return home_view(request, *args, **kwargs)


def ra_search(request, *args, **kwargs):
    try:
        site = get_object_or_404(Site, id=kwargs['siteid'])
        page = None
        compiled = "<div>"
        pagename = "/registered-agents/search/key/value"
        for i in site.pages:
            if i.route == pagename:
                page = i
                break
        if page == None:
            return home_view(request, *args, **kwargs)
        else:
            rep_args = dict()
            url_args = dict()
            for k, v in kwargs.items():
                if type(v) == str:
                    rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                    url_args[k] = re.sub('_', ' ', v)
            agents_objs = list(coll_ra.find({"$text":{"$search":url_args['query']}},{"score":{"$meta":"textScore"}}).sort([("score",{"$meta":"textScore"})]))
            agent_table = """
                <div class="table-responsive">
                    <table id="default_order" class="table table-striped table-bordered display" style="width:100%">
                        <thead>
                            <tr>
                                <th>Registered Agent</th>
                            </tr>
                        </thead>
                        <tbody>
                """
            for i in agents_objs:
                agent = re.sub(' ', '_', i['agent'])
                state = re.sub(' ', '_', i['state'])
                county = re.sub(' ', '_', i['county'])
                city = re.sub(' ', '_', i['city'])
                rel_link = urllib.parse.quote(f"/registered-agents/{agent}--{state}--{county}--{city}/{i['id']}/")
                agent_table += f"""<tr><td><a href="{rel_link}">{i['agent']} - {i['city']}, {i['stateacronym']}</a></td></tr>"""

            agent_table += """
                        </tbody>
                    </table>
                </div>
                """

            res = f"{basic_doc}"
            rep_codes = {
                'XXpagemetasXX': f"{page.pagemetas}",
                'XXpagelinksXX': f"{page.pagelinks}",
                'XXtitleXX': f"{page.title}",
                'XXcontentXX': f"{page.content}",
                'XXpagescriptsXX': f"{page.pagescripts}",
            }
            for k, v in rep_codes.items():
                res = re.sub(k, v, res)
            res = re.sub('XXagentsXX', agent_table, res)
            for k, v in rep_args.items():
                res = re.sub(k, v, res)
            res = replace_shortcodes(site, res)
            res = re.sub(r'XX\w+XX', '', res)
            return HttpResponse(res, content_type='text/html')
    except Exception as e:
        print(e)
        PrintException()
        return home_view(request, *args, **kwargs)

def ra_agent(request, *args, **kwargs):
    try:
        site = get_object_or_404(Site, id=kwargs['siteid'])
        page = None
        compiled = "<div>"
        pagename = "/registered-agents/id"
        for i in site.pages:
            if i.route == pagename:
                page = i
                break
        if page == None:
            return home_view(request, *args, **kwargs)
        else:
            rep_args = dict()
            url_args = dict()
            for k, v in kwargs.items():
                if type(v) == str:
                    rep_args[f"XX{k}XX"] = re.sub('_', ' ', v)
                    url_args[k] = re.sub('_', ' ', v)
            a_check = get_object_or_404(Agent, id=kwargs['agentid'])
            agents_objs = list(coll_ra.find({'id': kwargs['agentid']}, {'_id': 0}))[0]

            res = f"{basic_doc}"
            rep_codes = {
                'XXpagemetasXX': f"{page.pagemetas}",
                'XXpagelinksXX': f"{page.pagelinks}",
                'XXtitleXX': f"{page.title}",
                'XXcontentXX': f"{page.content}",
                'XXpagescriptsXX': f"{page.pagescripts}",
            }
            for k, v in rep_codes.items():
                res = re.sub(k, v, res)
            for k, v in agents_objs.items():
                res = re.sub(f"XX{k}XX", f"{v}", res)
            res = replace_shortcodes(site, res)
            res = re.sub(r'XX\w+XX', '', res)
            return HttpResponse(res, content_type='text/html')
    except Exception as e:
        print(e)
        PrintException()
        return home_view(request, *args, **kwargs)


@login_required
def upload_agents(request):
    with open(file_path) as f:
        data = json.load(f)
    for idx, val in enumerate(data):
        form = AgentModelForm(val)
        if form.is_valid():
            form.save()
    return HttpResponse("Success")

def compilerv4(request, siteid):
    s = Site.objects.get(id=siteid)
    rt = request.GET.get('route', '/')
    def contains(list, filter):
        for x in list:
            if filter(x):
                return x
        return False
    page = contains(s.pages, lambda x: x.route == rt)
    if type(page) is bool:
        raise Http404("this page does not exist")
    profile = request.user
    context = {
        'site': s,
        'profile': profile,
        'page': page
    }

    return render(request, 'agents/comp.html', context)


@login_required
def agent_create_and_list_view(request):
    qs = Agent.objects.all()
    profile = request.user

    # initials
    a_form = AgentModelForm()
    agent_added = False

    if 'submit_a_form' in request.POST:
        # print(request.POST)
        a_form = AgentModelForm(request.POST)
        if a_form.is_valid():
            instance = a_form.save(commit=False)
            instance.save()
            a_form = AgentModelForm()
            agent_added = True


    context = {
        'qs': qs,
        'profile': profile,
        'a_form': a_form,
        'agent_added': agent_added,
    }

    return render(request, 'agents/main.html', context)


class AgentDeleteView(LoginRequiredMixin, DeleteView):
    model = Agent
    template_name = 'agents/confirm_del.html'
    success_url = reverse_lazy('agents:main-agent-view')
    # success_url = '/agents/'

    def get_object(self, *args, **kwargs):
        pk = self.kwargs.get('pk')
        obj = Agent.objects.get(id=pk)
        return obj

class AgentUpdateView(LoginRequiredMixin, UpdateView):
    form_class = AgentModelForm
    model = Agent
    template_name = 'agents/update.html'
    success_url = reverse_lazy('agents:main-agent-view')

    def form_valid(self, form):
        return super().form_valid(form)
    
