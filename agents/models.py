from djongo import models
from django import forms

# Create your models here.
class Agent(models.Model):
    agent = models.TextField()
    state = models.TextField()
    stateacronym = models.TextField()
    county = models.TextField()
    city = models.TextField()
    zip = models.TextField()
    address = models.TextField()
    agenttype = models.TextField(blank=True, default="ra")
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    objects = models.DjongoManager()

    def __str__(self):
        return str(self.agent)

    class Meta:
        ordering = ('-created',)

