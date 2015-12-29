# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('kw_webapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='join_date',
            field=models.DateTimeField(default=datetime.datetime(2015, 12, 29, 6, 47, 35, 777929, tzinfo=utc)),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='profile',
            name='title',
            field=models.CharField(default='Turtles', max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='announcement',
            name='pub_date',
            field=models.DateTimeField(default=datetime.datetime(2015, 12, 29, 6, 47, 35, 777428, tzinfo=utc), null=True, verbose_name='Date Published'),
            preserve_default=True,
        ),
    ]
