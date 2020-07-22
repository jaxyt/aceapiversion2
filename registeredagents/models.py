from djongo import models
from django import forms

# Create your models here.
class RegisteredAgent(models.Model):
    company = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=200, blank=True)
    agency = models.CharField(max_length=200, blank=True)
    contact = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    mail = models.TextField(blank=True)
    phone = models.CharField(max_length=200, blank=True)
    fax = models.CharField(max_length=200, blank=True)
    email = models.CharField(max_length=200, blank=True)
    website = models.CharField(max_length=200, blank=True)

    objects = models.DjongoManager()


class Corporation(models.Model):
    name = models.CharField(max_length=200)
    searchkey = models.CharField(max_length=100)
    searchvalue = models.TextField()
    objects = models.DjongoManager()
