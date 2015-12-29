# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('kw_webapp', '0003_auto_20151229_0211'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='pub_date',
            field=models.DateTimeField(verbose_name='Date Published', default=datetime.datetime(2015, 12, 29, 7, 16, 23, 264582, tzinfo=utc), null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='profile',
            name='join_date',
            field=models.DateField(auto_now_add=True),
            preserve_default=True,
        ),
    ]
