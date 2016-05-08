# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kw_webapp', '0011_vacation_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='auto_expand_answer_on_success',
            field=models.BooleanField(default=False),
        ),
    ]
