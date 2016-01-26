# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kw_webapp', '0006_auto_20160121_1638'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='only_review_burned',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
