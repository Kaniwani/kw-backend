# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kw_webapp', '0009_userspecific_wanikani_burned'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='on_vacation',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='profile',
            name='vacation_date',
            field=models.DateTimeField(null=True, blank=True, default=None),
            preserve_default=True,
        ),
    ]
