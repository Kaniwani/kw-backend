# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kw_webapp', "0010_auto_20160207_2013"),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='vacation_date',
            field=models.DateTimeField(null=True, blank=True, default=None),
            preserve_default=True,
        ),
    ]
