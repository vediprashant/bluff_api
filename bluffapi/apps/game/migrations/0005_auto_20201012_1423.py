# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-10-12 08:53
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0004_auto_20201012_1418'),
    ]

    operations = [
        migrations.RenameField(
            model_name='gametablesnapshot',
            old_name='lastCards',
            new_name='last_cards',
        ),
    ]
