from djongo import models
from django import forms

# Create your models here.
class Blog(models.Model):

    blogtitle = models.CharField(max_length=200)
    bloguri = models.CharField(max_length=200, blank=True)
    blogcategory = models.CharField(max_length=200, blank=True)
    blogkeywords = models.TextField(blank=True)
    blogpost = models.TextField(blank=True)
    blogpostnational = models.TextField(blank=True)
    blogdate = models.DateTimeField(auto_now=True)
    blogauthor = models.TextField(default="Jon Levy")

    objects = models.DjongoManager()

