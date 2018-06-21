# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("kw_webapp", "0008_auto_20160123_1330")]

    operations = [
        migrations.AddField(
            model_name="userspecific",
            name="wanikani_burned",
            field=models.BooleanField(default=False),
            preserve_default=True,
        )
    ]
