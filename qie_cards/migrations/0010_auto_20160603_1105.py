# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-03 16:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qie_cards', '0009_auto_20160603_1056'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attempt',
            name='comments',
            field=models.CharField(blank=True, default='', max_length=1000),
        ),
        migrations.AlterField(
            model_name='qiecard',
            name='comments',
            field=models.CharField(blank=True, default='', max_length=1000),
        ),
    ]
