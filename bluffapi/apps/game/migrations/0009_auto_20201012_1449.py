# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-10-12 09:19
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0008_auto_20201012_1444'),
    ]

    operations = [
        migrations.RenameField(
            model_name='gametablesnapshot',
            old_name='bluffSuccessful',
            new_name='bluff_successful',
        ),
    ]
