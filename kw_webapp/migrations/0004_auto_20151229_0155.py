# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('kw_webapp', '0003_auto_20151229_0152'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='pub_date',
            field=models.DateTimeField(null=True, default=datetime.datetime(2015, 12, 29, 6, 55, 57, 572875, tzinfo=utc), verbose_name='Date Published'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='profile',
            name='join_date',
            field=models.DateField(default=datetime.datetime(2015, 12, 29, 6, 55, 57, 573804, tzinfo=utc)),
            preserve_default=True,
        ),
    ]
