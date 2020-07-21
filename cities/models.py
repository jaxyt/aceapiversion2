from djongo import models
from django import forms


# Create your models here.

class City(models.Model):
    stateid = models.IntegerField()
    statename = models.CharField(max_length=200)
    countyid = models.IntegerField()
    countyname = models.CharField(max_length=200)
    cityname = models.CharField(max_length=200)
    cityngram = models.TextField(blank=True)

    objects = models.DjongoManager()
