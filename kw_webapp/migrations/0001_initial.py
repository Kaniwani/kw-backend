# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime
import django.utils.timezone
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Announcement",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("body", models.TextField()),
                (
                    "pub_date",
                    models.DateTimeField(
                        default=datetime.datetime(
                            2016, 1, 10, 21, 15, 22, 895830, tzinfo=utc
                        ),
                        verbose_name="Date Published",
                        null=True,
                    ),
                ),
                ("creator", models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Level",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                (
                    "level",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(50),
                        ]
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("api_key", models.CharField(max_length=255)),
                ("gravatar", models.CharField(max_length=255)),
                (
                    "level",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(50),
                        ],
                        null=True,
                    ),
                ),
                (
                    "unlocked_levels",
                    models.ManyToManyField(to="kw_webapp.Level"),
                ),
                ("user", models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Reading",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("character", models.CharField(max_length=255)),
                ("kana", models.CharField(max_length=255)),
                (
                    "level",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(50),
                        ]
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="UserSpecific",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                (
                    "synonyms",
                    models.CharField(
                        default=None, blank=True, null=True, max_length=255
                    ),
                ),
                ("correct", models.PositiveIntegerField(default=0)),
                ("incorrect", models.PositiveIntegerField(default=0)),
                ("streak", models.PositiveIntegerField(default=0)),
                ("last_studied", models.DateTimeField(auto_now_add=True)),
                ("needs_review", models.BooleanField(default=True)),
                (
                    "unlock_date",
                    models.DateTimeField(
                        default=django.utils.timezone.now, blank=True
                    ),
                ),
                (
                    "next_review_date",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        blank=True,
                        null=True,
                    ),
                ),
                ("burnt", models.BooleanField(default=False)),
                ("user", models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Vocabulary",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("meaning", models.CharField(max_length=255)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name="userspecific",
            name="vocabulary",
            field=models.ForeignKey(to="kw_webapp.Vocabulary"),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="reading",
            name="vocabulary",
            field=models.ForeignKey(to="kw_webapp.Vocabulary"),
            preserve_default=True,
        ),
    ]
