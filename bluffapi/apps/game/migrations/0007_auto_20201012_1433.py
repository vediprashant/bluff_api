# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-10-12 09:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0006_auto_20201012_1428'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gametablesnapshot',
            name='currentUser',
        ),
        migrations.AddField(
            model_name='gametablesnapshot',
            name='current_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='current_user', to='game.GamePlayer'),
        ),
    ]
