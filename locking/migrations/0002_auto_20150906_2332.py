# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('locking', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='lock',
            name='expires_on',
            field=models.DateTimeField(default=datetime.datetime(2015, 9, 7, 3, 32, 8, 543000, tzinfo=utc), verbose_name='expires on', db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lock',
            name='renewed_on',
            field=models.DateTimeField(default=datetime.datetime(2015, 9, 7, 3, 32, 18, 56000, tzinfo=utc), verbose_name='renewed on', db_index=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='lock',
            name='created_on',
            field=models.DateTimeField(verbose_name='created on', db_index=True),
        ),
        migrations.AlterField(
            model_name='lock',
            name='max_age',
            field=models.PositiveIntegerField(default=0, help_text='The age of a lock before it can be overwritten. 0 means indefinitely.', verbose_name='Maximum lock age'),
        ),
    ]
