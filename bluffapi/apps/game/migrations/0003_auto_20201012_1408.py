# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-10-12 08:38
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0002_auto_20201012_1357'),
    ]

    operations = [
        migrations.RenameField(
            model_name='gametablesnapshot',
            old_name='currentSet',
            new_name='current_set',
        ),
    ]
