from django.http.response import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from .models import Agent
from .forms import AgentModelForm
from sites.models import Site
from templates.models import Template
from django.views.generic import UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
import os
import json
import re
# Create your views here.
module_dir = os.path.dirname(__file__)  # get current directory
file_path = os.path.join(module_dir, 'sop-to-mongo.json')


def compilerv5(request, *args, **kwargs):
    site = None
    page = None
    res = ""
    if kwargs['siteid']:
        site = get_object_or_404(Site, id=kwargs['siteid'])
    if kwargs['page']:
        if kwargs['page'] == 'blog':
            return Http404()
        agent_dynamics = ["process-server", "agents-by-state", "registered-agents"]
        try:
            agent_dynamics.index(kwargs['page'])
        except ValueError as e:
            print(e)
        if kwargs['page'] != 'process-server' and kwargs['page'] != 'agents-by-state' and kwargs['page'] != 'registered-agents':
            regx = re.compile("[\w\d-]+\.\w{2,4}")
            mime = re.search(regx, '/'.join(list(kwargs.values())))
            if mime is not None:
                print(mime.group())
                return Http404()
            page_rts = [i.route for i in site.pages]
            if page is None:
                return Http404()
            
            res += f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{site.sitename}</title>
</head>
<body>
    {page.content}
</body>
</html>"""
        else:
            fwargs = dict()
            for k,v in kwargs.items():
                if k != 'siteid' and k != 'page':
                    fwargs[k] = v
            if len(fwargs):
                if kwargs['page'] == 'process-server':
                    print("process server")
                elif kwargs['page'] == 'agents-by-state':
                    print("agents-by-state")
                elif kwargs['page'] == 'registered-agents':
                    print("registered-agents")
            """
            process-server - list all unique corporations
                id - list all unique states
                    state - list all unique counties and cities
                        city - list all selected agents locations in city
            agents-by-state - list all states
                state - list all unique agents in state and all unique cites in state
                    city - list all unique agents in city
            registered-agents - total list of agents (as json)
                id - individual agent info
            """
        
    return HttpResponse(res)


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
    