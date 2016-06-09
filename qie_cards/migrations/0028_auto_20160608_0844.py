# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-08 13:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('qie_cards', '0027_auto_20160607_1513'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attempt',
            name='test_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='qie_cards.Test'),
        ),
        migrations.AlterField(
            model_name='attempt',
            name='tester',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='qie_cards.Tester'),
        ),
    ]
