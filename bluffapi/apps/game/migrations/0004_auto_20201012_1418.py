# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-10-12 08:48
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0003_auto_20201012_1408'),
    ]

    operations = [
        migrations.RenameField(
            model_name='gametablesnapshot',
            old_name='cardsOnTable',
            new_name='cards_on_table',
        ),
    ]