# Generated by Django 2.2.12 on 2020-08-03 15:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registeredagents', '0005_registeredagent_city'),
    ]

    operations = [
        migrations.CreateModel(
            name='TelecomCorps',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('carriername', models.CharField(blank=True, max_length=200)),
                ('businessname', models.CharField(blank=True, max_length=200)),
                ('holdingcompany', models.CharField(blank=True, max_length=200)),
            ],
        ),
    ]
