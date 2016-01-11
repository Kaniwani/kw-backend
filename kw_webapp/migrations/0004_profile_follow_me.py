# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kw_webapp', '0003_auto_20160110_1715'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='follow_me',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
