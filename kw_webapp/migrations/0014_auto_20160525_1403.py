# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("kw_webapp", "0013_merge")]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="api_valid",
            field=models.BooleanField(default=True),
        )
    ]
