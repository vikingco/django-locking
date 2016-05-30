# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locking', '0003_optimize_queries'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nonblockinglock',
            name='max_age',
            field=models.PositiveIntegerField(default=600, help_text='The age of a lock before it can be overwritten. 0 means indefinitely.', verbose_name='Maximum lock age'),
        ),
    ]
