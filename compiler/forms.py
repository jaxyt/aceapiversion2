from django import forms
from ckeditor.fields import RichTextField
from sites.models import Site
from templates.models import Template
from blogs.models import Blog
from states.models import State
from counties.models import County
from cities.models import City
from registeredagents.models import RegisteredAgent, TelecomCorps

class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = '__all__'

class TemplateForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = '__all__'
        
class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = '__all__'

class StateForm(forms.ModelForm):
    class Meta:
        model = State
        fields = '__all__'
        
class CountyForm(forms.ModelForm):
    class Meta:
        model = County
        fields = '__all__'

class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = '__all__'

class RegisteredAgentForm(forms.ModelForm):
    class Meta:
        model = RegisteredAgent
        fields = '__all__'

class TelecomCorpsForm(forms.ModelForm):
    class Meta:
        model = TelecomCorps
        fields = '__all__'

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()

class RichForm(forms.Form):
    content = RichTextField(blank=True)
