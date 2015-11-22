# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import django.core.validators
import django.utils.timezone
from django.conf import settings
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('title', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('pub_date', models.DateTimeField(null=True, verbose_name='Date Published', default=datetime.datetime(2015, 11, 22, 6, 16, 34, 297053, tzinfo=utc))),
                ('creator', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Level',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('level', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(60)])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('api_key', models.CharField(max_length=255)),
                ('api_valid', models.BooleanField(default=False)),
                ('gravatar', models.CharField(max_length=255)),
                ('about', models.CharField(max_length=255, default='')),
                ('website', models.CharField(max_length=255, default='')),
                ('twitter', models.CharField(max_length=255, default='@Tadgh11')),
                ('topics_count', models.PositiveIntegerField(default=0)),
                ('posts_count', models.PositiveIntegerField(default=0)),
                ('level', models.PositiveIntegerField(null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(60)])),
                ('unlocked_levels', models.ManyToManyField(to='kw_webapp.Level')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Reading',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('character', models.CharField(max_length=255)),
                ('kana', models.CharField(max_length=255)),
                ('level', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(60)])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Synonym',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('text', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserSpecific',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('synonyms', models.CharField(null=True, max_length=255, blank=True, default=None)),
                ('correct', models.PositiveIntegerField(default=0)),
                ('incorrect', models.PositiveIntegerField(default=0)),
                ('streak', models.PositiveIntegerField(default=0)),
                ('last_studied', models.DateTimeField(auto_now_add=True)),
                ('needs_review', models.BooleanField(default=True)),
                ('unlock_date', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('next_review_date', models.DateTimeField(null=True, blank=True, default=django.utils.timezone.now)),
                ('burnt', models.BooleanField(default=False)),
                ('hidden', models.BooleanField(default=False)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Vocabulary',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('meaning', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='userspecific',
            name='vocabulary',
            field=models.ForeignKey(to='kw_webapp.Vocabulary'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='synonym',
            name='review',
            field=models.ForeignKey(null=True, to='kw_webapp.UserSpecific'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reading',
            name='vocabulary',
            field=models.ForeignKey(to='kw_webapp.Vocabulary'),
            preserve_default=True,
        ),
    ]
