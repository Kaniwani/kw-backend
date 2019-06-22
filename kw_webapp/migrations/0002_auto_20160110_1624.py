# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.core.validators
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("kw_webapp", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Synonym",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("text", models.CharField(max_length=255)),
                (
                    "review",
                    models.ForeignKey(null=True, to="kw_webapp.UserSpecific"),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.RemoveField(model_name="userspecific", name="synonyms"),
        migrations.AddField(
            model_name="profile",
            name="about",
            field=models.CharField(default="", max_length=255),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="profile",
            name="api_valid",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="profile",
            name="join_date",
            field=models.DateField(null=True, auto_now_add=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="profile",
            name="posts_count",
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="profile",
            name="title",
            field=models.CharField(
                null=True, max_length=255, default="Turtles"
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="profile",
            name="topics_count",
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="profile",
            name="twitter",
            field=models.CharField(default="N/A", max_length=255),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="profile",
            name="website",
            field=models.CharField(default="N/A", max_length=255),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="userspecific",
            name="hidden",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="announcement",
            name="pub_date",
            field=models.DateTimeField(
                null=True, auto_now_add=True, verbose_name="Date Published"
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="level",
            name="level",
            field=models.PositiveIntegerField(
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(60),
                ]
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="profile",
            name="level",
            field=models.PositiveIntegerField(
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(60),
                ],
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="reading",
            name="level",
            field=models.PositiveIntegerField(
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(60),
                ]
            ),
            preserve_default=True,
        ),
    ]
