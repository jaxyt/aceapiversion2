# Generated by Django 2.2.12 on 2020-04-24 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('states', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='state',
            name='statengram',
            field=models.TextField(blank=True),
        ),
    ]
