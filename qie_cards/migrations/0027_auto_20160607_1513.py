# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-07 20:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qie_cards', '0026_auto_20160607_0947'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attempt',
            name='image',
            field=models.ImageField(default='images/default.png', upload_to='images'),
        ),
    ]
