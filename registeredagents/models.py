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
    city = models.CharField(max_length=200, blank=True)

    objects = models.DjongoManager()


class Corporation(models.Model):
    name = models.CharField(max_length=200)
    searchkey = models.CharField(max_length=100)
    searchvalue = models.TextField()
    objects = models.DjongoManager()


class TelecomCorps(models.Model):
    carriername = models.CharField(max_length=200, blank=True)
    businessname = models.CharField(max_length=200, blank=True)
    holdingcompany = models.CharField(max_length=200, blank=True)
    hqaddress1 = models.CharField(max_length=200, blank=True)
    hqaddress2 = models.CharField(max_length=200, blank=True)
    hqaddress3 = models.CharField(max_length=200, blank=True)
    othertradename1 = models.CharField(max_length=200, blank=True)
    othertradename2 = models.CharField(max_length=200, blank=True)
    othertradename3 = models.CharField(max_length=200, blank=True)
    othertradename4 = models.CharField(max_length=200, blank=True)
    dcagent1 = models.CharField(max_length=200, blank=True)
    dcagent2 = models.CharField(max_length=200, blank=True)
    dcagentaddress1 = models.CharField(max_length=200, blank=True)
    dcagentaddress2 = models.CharField(max_length=200, blank=True)
    dcagentaddress3 = models.CharField(max_length=200, blank=True)
    dcagentcity = models.CharField(max_length=200, blank=True)
    dcagentstate = models.CharField(max_length=200, blank=True)
    dcagentzip = models.CharField(max_length=200, blank=True)
    alternateagent1 = models.CharField(max_length=200, blank=True)
    alternateagent2 = models.CharField(max_length=200, blank=True)
    alternateagenttelephone = models.CharField(max_length=200, blank=True)
    alternateagentext = models.CharField(max_length=200, blank=True)
    alternateagentfax = models.CharField(max_length=200, blank=True)
    alternateagentemail = models.CharField(max_length=200, blank=True)
    alternateagentaddress1 = models.CharField(max_length=200, blank=True)
    alternateagentaddress2 = models.CharField(max_length=200, blank=True)
    alternateagentaddress3 = models.CharField(max_length=200, blank=True)
    alternateagentcity = models.CharField(max_length=200, blank=True)
    alternateagentstate = models.CharField(max_length=200, blank=True)
    alternateagentzip = models.CharField(max_length=200, blank=True)
    note1 = models.CharField(max_length=200, blank=True)
    note2 = models.CharField(max_length=200, blank=True)
    note3 = models.CharField(max_length=200, blank=True)
