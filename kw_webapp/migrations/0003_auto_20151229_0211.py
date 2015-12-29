# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('kw_webapp', '0002_auto_20151229_0147'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='pub_date',
            field=models.DateTimeField(null=True, default=datetime.datetime(2015, 12, 29, 7, 11, 31, 769338, tzinfo=utc), verbose_name='Date Published'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='profile',
            name='join_date',
            field=models.DateField(default=datetime.datetime(2015, 12, 29, 7, 11, 31, 769839, tzinfo=utc)),
            preserve_default=True,
        ),
    ]
