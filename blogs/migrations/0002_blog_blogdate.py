# Generated by Django 2.2.12 on 2020-04-29 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blogs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='blog',
            name='blogdate',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
