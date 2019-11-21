# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,import-error,no-name-in-module,too-few-public-methods,no-member
"""Adding JSONB field for Node.attributes and Node.Extras"""

import math

import click
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
from django.db import transaction

from aiida.backends.djsite.db.migrations import upgrade_schema_version
from aiida.cmdline.utils import echo
from aiida.common.timezone import datetime_to_isoformat

REVISION = '1.0.37'
DOWN_REVISION = '1.0.36'

# Nodes are processes in groups of the following size
group_size = 1000


def lazy_bulk_fetch(max_obj, max_count, fetch_func, start=0):
    counter = start
    while counter < max_count:
        yield fetch_func()[counter:counter + max_obj]
        counter += max_obj


def transition_attributes_extras(apps, _):
    """ Migrate the DbAttribute & the DbExtras tables into the attributes and extras columns of DbNode. """
    db_node_model = apps.get_model('db', 'DbNode')

    with transaction.atomic():
        total_node_no = db_node_model.objects.count()

        if total_node_no == 0:
            return

        with click.progressbar(label='Updating attributes and extras', length=total_node_no, show_pos=True) as pr_bar:
            fetcher = lazy_bulk_fetch(group_size, total_node_no, db_node_model.objects.order_by('id').all)
            error = False

            for batch in fetcher:
                for curr_dbnode in batch:

                    # Migrating attributes
                    dbattrs = list(curr_dbnode.dbattributes.all())
                    attrs, err_ = attributes_to_dict(sorted(dbattrs, key=lambda a: a.key))
                    error |= err_
                    curr_dbnode.attributes = attrs

                    # Migrating extras
                    dbextr = list(curr_dbnode.dbextras.all())
                    extr, err_ = attributes_to_dict(sorted(dbextr, key=lambda a: a.key))
                    error |= err_
                    curr_dbnode.extras = extr

                    # Saving the result
                    curr_dbnode.save()
                    pr_bar.update(1)

                    if error:
                        raise Exception('There has been some errors during the migration')


def transition_settings(apps, _):
    """ Migrate the DbSetting EAV val into the JSONB val column of the same table. """
    db_setting_model = apps.get_model('db', 'DbSetting')

    with transaction.atomic():
        total_settings_no = db_setting_model.objects.count()

        if total_settings_no == 0:
            return

        with click.progressbar(label='Updating settings', length=total_settings_no, show_pos=True) as pr_bar:
            fetcher = lazy_bulk_fetch(group_size, total_settings_no, db_setting_model.objects.order_by('id').all)
            error = False

            for batch in fetcher:
                for curr_dbsetting in batch:

                    # Migrating dbsetting.val
                    dt = curr_dbsetting.datatype
                    val = None
                    if dt == 'txt':
                        val = curr_dbsetting.tval
                    elif dt == 'float':
                        val = curr_dbsetting.fval
                        if math.isnan(val) or math.isinf(val):
                            val = str(val)
                    elif dt == 'int':
                        val = curr_dbsetting.ival
                    elif dt == 'bool':
                        val = curr_dbsetting.bval
                    elif dt == 'date':
                        val = datetime_to_isoformat(curr_dbsetting.dval)

                    curr_dbsetting.val = val

                    # Saving the result
                    curr_dbsetting.save()
                    pr_bar.update(1)

                    if error:
                        raise Exception('There has been some errors during the migration')


def attributes_to_dict(attr_list):
    """
    Transform the attributes of a node into a dictionary. It assumes the key
    are ordered alphabetically, and that they all belong to the same node.
    """
    d = {}

    error = False
    for a in attr_list:
        try:
            tmp_d = select_from_key(a.key, d)
        except ValueError:
            echo.echo_error("Couldn't transfer attribute {} with key {} for dbnode {}".format(a.id, a.key, a.dbnode_id))
            error = True
            continue
        key = a.key.split('.')[-1]

        if isinstance(tmp_d, (list, tuple)):
            key = int(key)

        dt = a.datatype

        if dt == 'dict':
            tmp_d[key] = {}
        elif dt == 'list':
            tmp_d[key] = [None] * a.ival
        else:
            val = None
            if dt == 'txt':
                val = a.tval
            elif dt == 'float':
                val = a.fval
                if math.isnan(val) or math.isinf(val):
                    val = str(val)
            elif dt == 'int':
                val = a.ival
            elif dt == 'bool':
                val = a.bval
            elif dt == 'date':
                val = datetime_to_isoformat(a.dval)

            tmp_d[key] = val

    return d, error


def select_from_key(key, d):
    """
    Return element of the dict to do the insertion on. If it is foo.1.bar, it
    will return d["foo"][1]. If it is only foo, it will return d directly.
    """
    path = key.split('.')[:-1]

    tmp_d = d
    for p in path:
        if isinstance(tmp_d, (list, tuple)):
            tmp_d = tmp_d[int(p)]
        else:
            tmp_d = tmp_d[p]

    return tmp_d


class Migration(migrations.Migration):
    """
    This migration changes Django backend to support the JSONB fields.
    It is a schema migration that removes the DbAttribute and DbExtra
    tables and their reference to the DbNode tables and adds the
    corresponding JSONB columns to the DbNode table.
    It is also a data migration that transforms and adds the data of
    the DbAttribute and DbExtra tables to the JSONB columns to the
    DbNode table.
    """

    dependencies = [
        ('db', '0036_drop_computer_transport_params'),
    ]

    operations = [
        # ############################################
        # Migration of the Attribute and Extras tables
        # ############################################

        # Create the DbNode.attributes JSONB and DbNode.extras JSONB fields
        migrations.AddField(
            model_name='dbnode',
            name='attributes',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict, null=True),
        ),
        migrations.AddField(
            model_name='dbnode',
            name='extras',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict, null=True),
        ),
        # Migrate the data from the DbAttribute table to the JSONB field
        migrations.RunPython(transition_attributes_extras, reverse_code=migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name='dbattribute',
            unique_together=set([]),
        ),
        # Delete the DbAttribute table
        migrations.DeleteModel(name='DbAttribute',),
        migrations.AlterUniqueTogether(
            name='dbextra',
            unique_together=set([]),
        ),
        # Delete the DbExtra table
        migrations.DeleteModel(name='DbExtra',),

        # ###############################
        # Migration of the Settings table

        # ###############################
        # Create the DbSetting.val JSONB field
        migrations.AddField(
            model_name='dbsetting',
            name='val',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=None, null=True),
        ),
        # Migrate the data from the DbSetting EAV to the JSONB val field
        migrations.RunPython(transition_settings, reverse_code=migrations.RunPython.noop),

        # Delete the tval, fval, ival, bval, dval
        migrations.RemoveField(
            model_name='dbsetting',
            name='tval',
        ),
        migrations.RemoveField(
            model_name='dbsetting',
            name='fval',
        ),
        migrations.RemoveField(
            model_name='dbsetting',
            name='ival',
        ),
        migrations.RemoveField(
            model_name='dbsetting',
            name='bval',
        ),
        migrations.RemoveField(
            model_name='dbsetting',
            name='dval',
        ),
        migrations.RemoveField(
            model_name='dbsetting',
            name='datatype',
        ),
        migrations.AlterField(
            model_name='dbsetting',
            name='key',
            field=models.TextField(),
        ),
        migrations.AlterUniqueTogether(
            name='dbsetting',
            unique_together=set([]),
        ),
        migrations.AlterField(
            model_name='dbsetting',
            name='key',
            field=models.CharField(max_length=1024, db_index=True, unique=True),
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION),
    ]
