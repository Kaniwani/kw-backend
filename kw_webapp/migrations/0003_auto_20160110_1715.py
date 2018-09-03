# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("kw_webapp", "0002_auto_20160110_1624")]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="twitter",
            field=models.CharField(null=True, max_length=255, default="N/A"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="profile",
            name="website",
            field=models.CharField(null=True, max_length=255, default="N/A"),
            preserve_default=True,
        ),
    ]
