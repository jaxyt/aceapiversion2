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

class Page(models.Model):
    route = models.CharField(max_length=200)
    content = models.TextField()
    title = models.CharField(max_length=200)
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

class Template(models.Model):

    templatename = models.CharField(max_length=200)
    sitemetas = models.TextField(blank=True)
    sitelinks = models.TextField(blank=True)
    sitescripts = models.TextField(blank=True)
    sitestyle = models.TextField(blank=True)
    siteheader = models.TextField(blank=True)
    sitefooter = models.TextField(blank=True)
    templatenotes = models.TextField(blank=True)

    shortcodes = models.ArrayField(
        model_container=Shortcode,
        model_form_class=ShortcodeForm,
        blank=True
    )

    pages = models.ArrayField(
        model_container=Page,
        model_form_class=PageForm,
    )

    objects = models.DjongoManager()
