# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kw_webapp', '0004_profile_follow_me'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='auto_advance_on_success',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='profile',
            name='auto_expand_answer_on_failure',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
