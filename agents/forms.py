from django import forms
from .models import Agent

class AgentModelForm(forms.ModelForm):

    class Meta:
        model = Agent
        fields = ( 'agent', 'state', 'stateacronym', 'county', 'city', 'zip', 'address', 'agenttype' )

