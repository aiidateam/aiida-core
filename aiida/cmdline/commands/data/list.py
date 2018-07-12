# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This module provides list functionality to all data types
"""
import click
from aiida.orm.implementation import Group
from aiida.orm.user import User
from aiida.orm.backend import construct_backend
from aiida.cmdline.params import options

LIST_OPTIONS = [
    click.option(
        '-p',
        '--past-days',
        type=click.INT,
        default=None,
        help="Add a filter to show only datas"
        " created in the past N days"),
    click.option(
        '-A',
        '--all-users',
        is_flag=True,
        default=False,
        help="show for all users, rather than only for the"
        "current user"),
    options.RAW(),
]


def list_options(func):
    """
    Creates a decorator with all the options
    """
    for option in reversed(LIST_OPTIONS):
        func = option(func)

    # Additional options
    # For some weird reason, if the following options are added to the above
    # list they don't perform as expected (i.e. they stop being
    # MultipleValueOption)
    func = options.GROUPS()(func)

    return func


def query(datatype, project, past_days, group_pks, all_users):
    """
    Perform the query
    """
    import datetime

    from aiida.orm.querybuilder import QueryBuilder
    from aiida.utils import timezone

    backend = construct_backend()

    qbl = QueryBuilder()
    if all_users is False:
        user = backend.users.get_automatic_user()
        qbl.append(User, tag="creator", filters={"email": user.email})
    else:
        qbl.append(User, tag="creator")

    # If there is a time restriction
    data_filters = {}
    if past_days is not None:
        now = timezone.now()
        n_days_ago = now - datetime.timedelta(days=past_days)
        data_filters.update({"ctime": {'>=': n_days_ago}})

    qbl.append(datatype, tag="data", created_by="creator", filters=data_filters, project=project)

    # If there is a group restriction
    if group_pks is not None:
        group_filters = dict()
        group_filters.update({"id": {"in": group_pks}})
        qbl.append(Group, tag="group", filters=group_filters, group_of="data")

    qbl.order_by({datatype: {'ctime': 'asc'}})

    object_list = qbl.distinct()
    return object_list.all()


# pylint: disable=unused-argument,too-many-arguments
def _list(datatype, columns, elements, elements_only, formulamode, past_days, groups, all_users):
    """
    List stored objects
    """
    columns_dict = {
        'ID': 'id',
        'Id': 'id',
        'Ctime': 'ctime',
        'Label': 'label',
        'Formula': 'attributes.formula',
        'Kinds': 'attributes.kinds',
        'Sites': 'attributes.sites',
        'Formulae': 'attributes.formulae',
        'Source': 'attributes.source',
        'Source.URI': 'attributes.source.uri',
    }
    project = [columns_dict[k] for k in columns]
    group_pks = None
    if groups is not None:
        group_pks = [g.pk for g in groups]
    return query(datatype, project, past_days, group_pks, all_users)
