# Generated by Django 2.2.12 on 2020-11-16 22:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0003_site_sitenotes'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='facebookurl',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='site',
            name='linkedinurl',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='site',
            name='logoheight',
            field=models.IntegerField(default=39),
        ),
        migrations.AddField(
            model_name='site',
            name='logoroute',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='site',
            name='logowidth',
            field=models.IntegerField(default=104),
        ),
        migrations.AddField(
            model_name='site',
            name='organizationname',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='site',
            name='searchroute',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='site',
            name='sitedescription',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='site',
            name='sitedisplayname',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='site',
            name='twitterusername',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
