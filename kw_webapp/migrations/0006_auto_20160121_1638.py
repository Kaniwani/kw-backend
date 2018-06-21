# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("kw_webapp", "0005_auto_20160114_1358")]

    operations = [
        migrations.AddField(
            model_name="userspecific",
            name="wanikani_srs",
            field=models.CharField(default="unknown", max_length=255),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="userspecific",
            name="wanikani_srs_numeric",
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
    ]
