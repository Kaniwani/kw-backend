# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("kw_webapp", "0007_profile_only_review_burned")]

    operations = [
        migrations.RenameField(
            model_name="userspecific", old_name="burnt", new_name="burned"
        )
    ]
