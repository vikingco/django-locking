# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NonBlockingLock',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('locked_object', models.CharField(unique=True, max_length=255, verbose_name='locked object')),
                ('created_on', models.DateTimeField(verbose_name='created on', db_index=True)),
                ('renewed_on', models.DateTimeField(verbose_name='renewed on', db_index=True)),
                ('expires_on', models.DateTimeField(verbose_name='expires on', db_index=True)),
                ('max_age', models.PositiveIntegerField(default=600, help_text='The age of a lock before it can be overwritten. 0 means indefinitely.', verbose_name='Maximum lock age')),
            ],
            options={
                'ordering': ['created_on'],
                'verbose_name': 'NonBlockingLock',
                'verbose_name_plural': 'NonBlockingLocks',
            },
        ),
    ]
