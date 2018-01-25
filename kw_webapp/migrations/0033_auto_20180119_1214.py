# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-01-19 17:14
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kw_webapp', '0032_auto_20171218_0826'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='auto_advance_on_success_delay_milliseconds',
            field=models.PositiveIntegerField(default=1000),
        ),
        migrations.AddField(
            model_name='profile',
            name='kanji_svg_draw_speed',
            field=models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)]),
        ),
        migrations.AddField(
            model_name='profile',
            name='show_kanji_svg_grid',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='profile',
            name='show_kanji_svg_stroke_order',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='profile',
            name='use_eijiro_pro_link',
            field=models.BooleanField(default=False),
        ),
    ]