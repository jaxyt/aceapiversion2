# Generated by Django 2.2.12 on 2020-07-29 20:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('states', '0002_state_statengram'),
    ]

    operations = [
        migrations.AddField(
            model_name='state',
            name='stateacronym',
            field=models.CharField(blank=True, max_length=5),
        ),
    ]
