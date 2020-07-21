from djongo import models
from django import forms


# Create your models here.

class County(models.Model):
    stateid = models.IntegerField()
    statename = models.CharField(max_length=200)
    countyname = models.CharField(max_length=200)
    countyngram = models.TextField(blank=True)

    objects = models.DjongoManager()

