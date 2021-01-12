from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from .models import Agent
from .forms import AgentModelForm
from sites.models import Site
from django.views.generic import UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
# Create your views here.


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

def compilerv4(request, siteid):
    s = Site.objects.get(id=siteid)
    profile = request.user
    context = {
        'site': s,
        'profile': profile
    }

    return render(request, 'agents/comp.html', context)

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
    