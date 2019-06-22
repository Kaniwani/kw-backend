# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("kw_webapp", "0014_auto_20160525_1403")]

    operations = [
        migrations.AlterField(
            model_name="reading",
            name="level",
            field=models.PositiveIntegerField(
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(60),
                ],
                null=True,
            ),
        )
    ]
