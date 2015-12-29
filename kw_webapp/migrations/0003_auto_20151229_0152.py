# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('kw_webapp', '0002_auto_20151229_0147'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='pub_date',
            field=models.DateTimeField(default=datetime.datetime(2015, 12, 29, 6, 52, 14, 615062, tzinfo=utc), verbose_name='Date Published', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='profile',
            name='join_date',
            field=models.DateTimeField(default=datetime.datetime(2015, 12, 29, 6, 52, 14, 616007, tzinfo=utc)),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='profile',
            name='twitter',
            field=models.CharField(default='N/A', max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='profile',
            name='website',
            field=models.CharField(default='N/A', max_length=255),
            preserve_default=True,
        ),
    ]
