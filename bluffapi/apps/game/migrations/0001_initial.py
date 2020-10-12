# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-10-11 11:30
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('started', models.BooleanField(default=False)),
                ('decks', models.PositiveIntegerField(default=1)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owner', to=settings.AUTH_USER_MODEL)),
                ('winner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='winner', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GamePlayer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('player_id', models.PositiveIntegerField(blank=True, null=True)),
                ('disconnected', models.BooleanField(default=True)),
                ('noAction', models.PositiveIntegerField(default=0)),
                ('cards', models.CharField(max_length=156)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.Game')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='GameTableSnapshot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('currentSet', models.PositiveIntegerField(blank=True, null=True)),
                ('cardsOnTable', models.CharField(max_length=156)),
                ('lastCards', models.CharField(max_length=156)),
                ('bluffSuccessful', models.NullBooleanField()),
                ('didSkip', models.NullBooleanField()),
                ('bluffCaller', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bluffCaller', to='game.GamePlayer')),
                ('currentUser', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='currentUser', to='game.GamePlayer')),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.Game')),
                ('lastUser', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lastUser', to='game.GamePlayer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterUniqueTogether(
            name='gameplayer',
            unique_together=set([('user', 'game')]),
        ),
    ]
