# Generated by Django 2.2.12 on 2020-04-13 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stateid', models.IntegerField()),
                ('statename', models.CharField(max_length=200)),
                ('countyid', models.IntegerField()),
                ('countyname', models.CharField(max_length=200)),
                ('cityname', models.CharField(max_length=200)),
            ],
        ),
    ]
