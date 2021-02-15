from django.http.response import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.http import Http404
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
import os
import json
import re
from .functions import PrintException, static_page, resource_page, individual_agent, agents_by_location, agents_by_corp, agents_query, blog_handler, sitemap_generator
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

test_doc = """<!DOCTYPE html>
    <html lang="en">
    <head>
        <title>XXroutetitleXX</title>
    </head>
    <body>
        XXtestcontentXX
    </body>
    </html>"""


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_home(request, *args, **kwargs):
    try:
        site = None
        page = None
        res = None
        dbg = False
        admin = False
        if request.GET.get('ip', '') == "66.229.0.114":
            admin = True
        if request.GET.get('dbg', '') == 'y':
            dbg = True
        default_response = "hello world"
        if kwargs['siteid']:
            site = get_object_or_404(Site, id=kwargs['siteid'])
            regx = re.compile("^/$")
            for i in site.pages:
                if re.search(regx, i.route):
                    page = i
                    break
            if page is None:
                return HttpResponseNotFound()
            res = static_page(request, site, page, dbg, admin, **kwargs)
            return res
        return HttpResponse(default_response, content_type="text/html")
    except Exception as e:
        print(e)
        PrintException()
        return HttpResponse("encountered exception", content_type="text/plain")

def compilerv5(request, *args, **kwargs):
    try:
        site = None
        page = None
        res = None
        pagename = ""
        dbg = False
        admin = False
        if request.GET.get('ip', '') == "66.229.0.114":
            admin = True
        if request.GET.get('dbg', '') == 'y':
            dbg = True
        default_response = "hello world"
        if kwargs['siteid']:
            site = get_object_or_404(Site, id=kwargs['siteid'])
        if kwargs['page']:
            regx = re.compile(f"(?<=compile/{kwargs['siteid']}/).*")
            pagename = re.search(regx, request.path).group()
            if kwargs['page'] == 'blog':
                try:
                    kwargs['blog_id']
                except KeyError as e:
                    regx = re.compile("^/blog/posts$")
                    for i in site.pages:
                        if re.search(regx, i.route):
                            page = i
                            break
                    res = static_page(request, site, page, dbg, admin, **kwargs)
                    return res
                else:
                    fwargs = dict()
                    for k,v in kwargs.items():
                        if k != 'siteid' and k != 'page':
                            fwargs[k] = v
                    res = blog_handler(request, site, pagename, dbg, admin, **fwargs)
                    return res
            if kwargs['page'] == 'sitemap.xml':
                res = sitemap_generator(request, site)
                return res
            agents_dynamics = ['process-server', 'registered-agents', 'agents-by-state']
            try:
                agents_dynamics.index(kwargs['page'])
            except ValueError as e:
                regx = re.compile(f"^/{kwargs['page']}$")
                for i in site.pages:
                    if re.search(regx, i.route):
                        page = i
                        break
                regx = re.compile("[\w-]+\.\w{2,4}")
                mime = re.search(regx, kwargs['page'])
                if mime is not None:
                    print(mime.group())
                    res = resource_page(request, site, page, **kwargs)
                    return res
                if page is None:
                    return get_home(request, *args, **kwargs)
                res = static_page(request, site, page, dbg, admin, **kwargs)
                return res
            else:
                fwargs = dict()
                for k,v in kwargs.items():
                    if k != 'siteid' and k != 'page':
                        fwargs[k] = v
                if kwargs['page'] == 'agents-by-state' and len(kwargs) == 2:
                    regx = re.compile("^/agents-by-state$")
                    for i in site.pages:
                        if re.search(regx, i.route):
                            page = i
                            break
                    res = static_page(request, site, page, dbg, admin, **kwargs)
                    return res
                if len(fwargs):
                    if kwargs['page'] == 'process-server':
                        res = agents_by_corp(request, site, pagename, dbg, admin, **fwargs)
                    elif kwargs['page'] == 'agents-by-state':
                        res = agents_by_location(request, site, pagename, dbg, admin, **fwargs)
                    elif kwargs['page'] == 'registered-agents':
                        for k, v in kwargs.items():
                            if k == 'agent':
                                res = individual_agent(request, site, pagename, dbg, admin, **fwargs)
                                return res
                        res = agents_query(request, site, pagename, dbg, admin, **fwargs)
                    return res
        return HttpResponse(default_response, content_type="text/html")
    except Exception as e:
        print(e)
        PrintException()
        return get_home(request, *args, **kwargs)


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
    try:
        print(request.META)
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
    except Exception as e:
        print(e)
        PrintException()


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
    
