# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-10-15 12:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_staff',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]
