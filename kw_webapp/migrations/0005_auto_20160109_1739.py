# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kw_webapp', '0004_auto_20151229_0155'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userspecific',
            name='synonyms',
        ),
        migrations.AlterField(
            model_name='announcement',
            name='pub_date',
            field=models.DateTimeField(verbose_name='Date Published', null=True, auto_now_add=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='profile',
            name='join_date',
            field=models.DateField(auto_now_add=True),
            preserve_default=True,
        ),
    ]
