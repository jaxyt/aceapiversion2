from djongo import models
from django import forms

# Create your models here.

class State(models.Model):

    statename = models.CharField(max_length=200)
    stateacronym = models.CharField(max_length=5, blank=True)
    statengram = models.TextField(blank=True)

    objects = models.DjongoManager()

