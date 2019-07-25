# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-few-public-methods
"""Initial schema of schema generation 2."""
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error,no-member
from django.conf import settings
from django.contrib.postgres.fields import jsonb
from django.db import models, migrations

from aiida.backends.djsite.db.migrations import upgrade_schema_version, upgrade_schema_generation
from aiida.common import timezone
from aiida.common.utils import get_new_uuid

REVISION = '2.1'
DOWN_REVISION = '2.0'


class Migration(migrations.Migration):
    """Initial schema of schema generation 2."""

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='DbUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(db_index=True, max_length=254, unique=True)),
                ('first_name', models.CharField(blank=True, max_length=254)),
                ('last_name', models.CharField(blank=True, max_length=254)),
                ('institution', models.CharField(blank=True, max_length=254)),
            ],
        ),
        migrations.CreateModel(
            name='DbAuthInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('auth_params', jsonb.JSONField(default=dict)),
                ('metadata', jsonb.JSONField(default=dict)),
                ('enabled', models.BooleanField(default=True)),
                ('aiidauser', models.ForeignKey(on_delete=models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DbComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=get_new_uuid, unique=True)),
                ('ctime', models.DateTimeField(default=timezone.now, editable=False)),
                ('mtime', models.DateTimeField(auto_now=True)),
                ('content', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='DbComputer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=get_new_uuid, unique=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('hostname', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('scheduler_type', models.CharField(max_length=255)),
                ('transport_type', models.CharField(max_length=255)),
                ('metadata', jsonb.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='DbGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=get_new_uuid, unique=True)),
                ('label', models.CharField(db_index=True, max_length=255)),
                ('type_string', models.CharField(db_index=True, default='', max_length=255)),
                ('time', models.DateTimeField(default=timezone.now, editable=False)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='DbLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(db_index=True, max_length=255)),
                ('type', models.CharField(blank=True, db_index=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='DbLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=get_new_uuid, unique=True)),
                ('time', models.DateTimeField(default=timezone.now, editable=False)),
                ('loggername', models.CharField(db_index=True, max_length=255)),
                ('levelname', models.CharField(db_index=True, max_length=50)),
                ('message', models.TextField(blank=True)),
                ('metadata', jsonb.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='DbNode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=get_new_uuid, unique=True)),
                ('node_type', models.CharField(db_index=True, max_length=255)),
                ('process_type', models.CharField(db_index=True, max_length=255, null=True)),
                ('label', models.CharField(blank=True, db_index=True, max_length=255)),
                ('description', models.TextField(blank=True)),
                ('ctime', models.DateTimeField(db_index=True, default=timezone.now, editable=False)),
                ('mtime', models.DateTimeField(auto_now=True, db_index=True)),
                ('attributes', jsonb.JSONField(default=dict, null=True)),
                ('extras', jsonb.JSONField(default=dict, null=True)),
                (
                    'dbcomputer',
                    models.ForeignKey(
                        null=True, on_delete=models.deletion.PROTECT, related_name='dbnodes', to='db.DbComputer'
                    )
                ),
                ('outputs', models.ManyToManyField(related_name='inputs', through='db.DbLink', to='db.DbNode')),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=models.deletion.PROTECT, related_name='dbnodes', to=settings.AUTH_USER_MODEL
                    )
                ),
            ],
        ),
        migrations.CreateModel(
            name='DbSetting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(db_index=True, max_length=1024, unique=True)),
                ('val', jsonb.JSONField(default=None, null=True)),
                ('description', models.TextField(blank=True)),
                ('time', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='dblog',
            name='dbnode',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='dblogs', to='db.DbNode'),
        ),
        migrations.AddField(
            model_name='dblink',
            name='input',
            field=models.ForeignKey(on_delete=models.deletion.PROTECT, related_name='output_links', to='db.DbNode'),
        ),
        migrations.AddField(
            model_name='dblink',
            name='output',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='input_links', to='db.DbNode'),
        ),
        migrations.AddField(
            model_name='dbgroup',
            name='dbnodes',
            field=models.ManyToManyField(related_name='dbgroups', to='db.DbNode'),
        ),
        migrations.AddField(
            model_name='dbgroup',
            name='user',
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE, related_name='dbgroups', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='dbcomment',
            name='dbnode',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='dbcomments', to='db.DbNode'),
        ),
        migrations.AddField(
            model_name='dbcomment',
            name='user',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='dbauthinfo',
            name='dbcomputer',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='db.DbComputer'),
        ),
        migrations.AlterUniqueTogether(
            name='dbgroup',
            unique_together=set([('label', 'type_string')]),
        ),
        migrations.AlterUniqueTogether(
            name='dbauthinfo',
            unique_together=set([('aiidauser', 'dbcomputer')]),
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION),
        upgrade_schema_generation('2')
    ]
