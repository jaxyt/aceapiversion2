from djongo import models
from django import forms

# Create your models here.
class Shortcode(models.Model):
    name = models.CharField(max_length=200, blank=True)
    value = models.TextField(blank=True)

    class Meta:
        abstract = True

class ShortcodeForm(forms.ModelForm):
    class Meta:
        model = Shortcode
        fields = (
            'name', 'value'
        )

class Location(models.Model):
    stateid = models.IntegerField(blank=True)
    statename = models.CharField(max_length=200, blank=True)
    countyid = models.IntegerField(blank=True)
    countyname = models.CharField(max_length=200, blank=True)
    cityid = models.IntegerField(blank=True)
    cityname = models.CharField(max_length=200, blank=True)

    class Meta:
        abstract = True

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = (
            'stateid', 'statename', 'countyid', 'countyname', 'cityid', 'cityname'
        )

class Page(models.Model):
    route = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    title = models.CharField(max_length=200, blank=True)
    pagemetas = models.TextField(blank=True)
    pagelinks = models.TextField(blank=True)
    pagescripts = models.TextField(blank=True)
    pagestyle = models.TextField(blank=True)
    pageheader = models.TextField(blank=True)
    pagefooter = models.TextField(blank=True)

    class Meta:
        abstract = True

class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = (
            'route', 'title', 'pagemetas', 'pagelinks', 'pagescripts', 'pagestyle', 'pageheader', 'pagefooter', 'content'
        )

class Site(models.Model):
    sitename = models.CharField(max_length=200)
    sitedisplayname = models.CharField(max_length=200, blank=True)
    organizationname = models.CharField(max_length=200, blank=True)
    sitedescription = models.TextField(blank=True)
    siteauthor = models.CharField(max_length=200, blank=True)
    facebookurl = models.TextField(blank=True)
    twitterusername = models.CharField(max_length=200, blank=True)
    linkedinurl = models.TextField(blank=True)
    searchroute = models.TextField(blank=True)
    logoroute = models.TextField(blank=True)
    logowidth = models.IntegerField(default=104)
    logoheight = models.IntegerField(default=39)
    templateid = models.IntegerField()
    sitemetas = models.TextField(blank=True)
    sitelinks = models.TextField(blank=True)
    sitescripts = models.TextField(blank=True)
    sitestyle = models.TextField(blank=True)
    siteheader = models.TextField(blank=True)
    sitefooter = models.TextField(blank=True)
    sitenotes = models.TextField(blank=True)
    blogcategory = models.CharField(max_length=200, blank=True)
    national = models.BooleanField(default=True)

    shortcodes = models.ArrayField(
        model_container=Shortcode,
        model_form_class=ShortcodeForm,
        blank=True
    )

    location = models.EmbeddedField(
        model_container=Location,
        model_form_class=LocationForm,
        blank=True
    )

    pages = models.ArrayField(
        model_container=Page,
        model_form_class=PageForm
    )

    objects = models.DjongoManager()

