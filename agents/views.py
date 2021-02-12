from django.http.response import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
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
from .functions import PrintException, static_page, resource_page, individual_agent, agents_by_location, agents_by_corp, agents_query, telecom_query, blog_handler, sitemap_generator
# Create your views here.
module_dir = os.path.dirname(__file__)  # get current directory
file_path = os.path.join(module_dir, 'sop-to-mongo.json')

four_oh_four = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>404 Not Found</title>
    <style>
        @import url(https://fonts.googleapis.com/css?family=opensans:500);
            body{
                /*background: #33cc99;*/
                background: #233242;
                color:#fff;
                font-family: 'Open Sans', sans-serif;
                max-height:700px;
                overflow: hidden;
            }
            .c{
                text-align: center;
                display: block;
                position: relative;
                width:80%;
                margin:100px auto;
            }
            ._404{
                font-size: 220px;
                position: relative;
                display: inline-block;
                z-index: 2;
                height: 250px;
                letter-spacing: 15px;
            }
            ._1{
                text-align:center;
                display:block;
                position:relative;
                letter-spacing: 12px;
                font-size: 4em;
                line-height: 80%;
            }
            ._2{
                text-align:center;
                display:block;
                position: relative;
                font-size: 20px;
            }
            .text{
                font-size: 70px;
                text-align: center;
                position: relative;
                display: inline-block;
                margin: 19px 0px 0px 0px;
                /* top: 256.301px; */
                z-index: 3;
                width: 100%;
                line-height: 1.2em;
                display: inline-block;
            }
        
            .btn{
                background-color: rgb( 255, 255, 255 );
                position: relative;
                display: inline-block;
                width: 358px;
                padding: 5px;
                z-index: 5;
                font-size: 25px;
                margin:0 auto;
                /*color:#33cc99;*/
                color:#233242;
                text-decoration: none;
                margin-right: 10px
            }
            .right{
                float:right;
                width:60%;
            }
            
            hr{
                padding: 0;
                border: none;
                border-top: 5px solid #fff;
                color: #fff;
                text-align: center;
                margin: 0px auto;
                width: 420px;
                height:10px;
                z-index: -10;
            }
            
            hr:after {
                content: "\\2022";
                display: inline-block;
                position: relative;
                top: -0.75em;
                font-size: 2em;
                padding: 0 0.2em;
                /*background: #33cc99;*/
                background: #233242;
            }
            
            .cloud {
                width: 350px; height: 120px;

                background: #FFF;
                background: linear-gradient(top, #FFF 100%);
                background: -webkit-linear-gradient(top, #FFF 100%);
                background: -moz-linear-gradient(top, #FFF 100%);
                background: -ms-linear-gradient(top, #FFF 100%);
                background: -o-linear-gradient(top, #FFF 100%);

                border-radius: 100px;
                -webkit-border-radius: 100px;
                -moz-border-radius: 100px;

                position: absolute;
                margin: 120px auto 20px;
                z-index:-1;
                transition: ease 1s;
            }

            .cloud:after, .cloud:before {
                content: '';
                position: absolute;
                background: #FFF;
                z-index: -1
            }

            .cloud:after {
                width: 100px; height: 100px;
                top: -50px; left: 50px;

                border-radius: 100px;
                -webkit-border-radius: 100px;
                -moz-border-radius: 100px;
            }

            .cloud:before {
                width: 180px; height: 180px;
                top: -90px; right: 50px;

                border-radius: 200px;
                -webkit-border-radius: 200px;
                -moz-border-radius: 200px;
            }
            
            .x1 {
                top:-50px;
                left:100px;
                -webkit-transform: scale(0.3);
                -moz-transform: scale(0.3);
                transform: scale(0.3);
                opacity: 0.9;
                -webkit-animation: moveclouds 15s linear infinite;
                -moz-animation: moveclouds 15s linear infinite;
                -o-animation: moveclouds 15s linear infinite;
            }
            
            .x1_5{
                top:-80px;
                left:250px;
                -webkit-transform: scale(0.3);
                -moz-transform: scale(0.3);
                transform: scale(0.3);
                -webkit-animation: moveclouds 17s linear infinite;
                -moz-animation: moveclouds 17s linear infinite;
                -o-animation: moveclouds 17s linear infinite; 
            }

            .x2 {
                left: 250px;
                top:30px;
                -webkit-transform: scale(0.6);
                -moz-transform: scale(0.6);
                transform: scale(0.6);
                opacity: 0.6; 
                -webkit-animation: moveclouds 25s linear infinite;
                -moz-animation: moveclouds 25s linear infinite;
                -o-animation: moveclouds 25s linear infinite;
            }

            .x3 {
                left: 250px; bottom: -70px;

                -webkit-transform: scale(0.6);
                -moz-transform: scale(0.6);
                transform: scale(0.6);
                opacity: 0.8; 

                -webkit-animation: moveclouds 25s linear infinite;
                -moz-animation: moveclouds 25s linear infinite;
                -o-animation: moveclouds 25s linear infinite;
            }

            .x4 {
                left: 470px; botttom: 20px;

                -webkit-transform: scale(0.75);
                -moz-transform: scale(0.75);
                transform: scale(0.75);
                opacity: 0.75;

                -webkit-animation: moveclouds 18s linear infinite;
                -moz-animation: moveclouds 18s linear infinite;
                -o-animation: moveclouds 18s linear infinite;
            }

            .x5 {
                left: 200px; top: 300px;

                -webkit-transform: scale(0.5);
                -moz-transform: scale(0.5);
                transform: scale(0.5);
                opacity: 0.8; 

                -webkit-animation: moveclouds 20s linear infinite;
                -moz-animation: moveclouds 20s linear infinite;
                -o-animation: moveclouds 20s linear infinite;
            }

            @-webkit-keyframes moveclouds {
                0% {margin-left: 1000px;}
                100% {margin-left: -1000px;}
            }
            @-moz-keyframes moveclouds {
                0% {margin-left: 1000px;}
                100% {margin-left: -1000px;}
            }
            @-o-keyframes moveclouds {
                0% {margin-left: 1000px;}
                100% {margin-left: -1000px;}
            }
    </style>
</head>
<body>
    <div id="clouds">
            <div class="cloud x1"></div>
            <div class="cloud x1_5"></div>
            <div class="cloud x2"></div>
            <div class="cloud x3"></div>
            <div class="cloud x4"></div>
            <div class="cloud x5"></div>
    </div>
    <div class='c'>
        <div class='_404'>404</div>
        <hr>
        <div class='_1'>THE PAGE</div>
        <div class='_2'>WAS NOT FOUND</div>
        <a class='btn' href='/'>BACK TO HOME</a>
    </div>
</body>
</html>
"""


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
                return HttpResponse(four_oh_four, content_type="text/html")
            res = static_page(request, site, page, dbg, admin, **kwargs)
            return res
        return HttpResponse(default_response, content_type="text/html")
    except Exception as e:
        print(e)
        PrintException()
        return HttpResponse(four_oh_four, content_type="text/html")

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
            agents_dynamics = ['process-server', 'registered-agents', 'agents-by-state', 'telecom-agents']
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
                    return HttpResponse(four_oh_four, content_type="text/html")
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
                    elif kwargs['page'] == 'telecom-agents':
                        if len(fwargs) > 1:
                            res = telecom_query(request, site, pagename, dbg, admin, **fwargs)
                    return res
        return HttpResponse(four_oh_four, content_type="text/html")
    except Exception as e:
        print(e)
        PrintException()
        return HttpResponse(four_oh_four, content_type="text/html")


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
    