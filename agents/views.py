from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from .models import Agent
from .forms import AgentModelForm
from sites.models import Site
from django.views.generic import UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
import os
import json
# Create your views here.
module_dir = os.path.dirname(__file__)  # get current directory
file_path = os.path.join(module_dir, 'sop-to-mongo.json')


def compilerv5(request, *args, **kwargs):
    print(kwargs)
    return HttpResponse("hello world")


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
    