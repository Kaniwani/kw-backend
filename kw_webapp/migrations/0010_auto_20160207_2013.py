# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("kw_webapp", "0009_userspecific_wanikani_burned")]

    operations = [
        migrations.CreateModel(
            name="AnswerSynonym",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        verbose_name="ID",
                        serialize=False,
                    ),
                ),
                ("character", models.CharField(max_length=255, null=True)),
                ("kana", models.CharField(max_length=255)),
                (
                    "review",
                    models.ForeignKey(to="kw_webapp.UserSpecific", null=True),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.RenameModel(old_name="Synonym", new_name="MeaningSynonym"),
    ]
