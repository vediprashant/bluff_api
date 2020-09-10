# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-09-10 12:33
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
                ('url', models.CharField(max_length=255)),
                ('inProgress', models.BooleanField(default=False)),
                ('gameStarted', models.BooleanField(default=False)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owner', to=settings.AUTH_USER_MODEL)),
                ('winner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='winner', to=settings.AUTH_USER_MODEL)),
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
                ('player_id', models.PositiveIntegerField()),
                ('disconnected', models.BooleanField(default=False)),
                ('noAction', models.PositiveIntegerField()),
                ('cards', models.BinaryField(max_length=156)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.Game')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GameTableSnapshot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('currentSet', models.PositiveIntegerField()),
                ('cardsOnTable', models.BinaryField(max_length=156)),
                ('lastCards', models.BinaryField(max_length=156)),
                ('bluffSuccessful', models.NullBooleanField()),
                ('didSkip', models.NullBooleanField()),
                ('bluffCaller', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bluffCaller', to='game.GamePlayer')),
                ('currentUser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='currentUser', to='game.GamePlayer')),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.Game')),
                ('lastUser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lastUser', to='game.GamePlayer')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
