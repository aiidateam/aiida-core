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
This module provides list functionality to all data types.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.cmdline.params import options

LIST_OPTIONS = [
    options.GROUPS,
    options.PAST_DAYS,
    options.ALL_USERS,
    options.RAW,
]


def list_options(func):
    """Creates a decorator with all the options."""
    for option in reversed(LIST_OPTIONS):
        func = option()(func)

    return func


def query(datatype, project, past_days, group_pks, all_users):
    """
    Perform the query
    """
    import datetime

    from aiida import orm
    from aiida.common import timezone

    qbl = orm.QueryBuilder()
    if all_users is False:
        user = orm.User.objects.get_default()
        qbl.append(orm.User, tag="creator", filters={"email": user.email})
    else:
        qbl.append(orm.User, tag="creator")

    # If there is a time restriction
    data_filters = {}
    if past_days is not None:
        now = timezone.now()
        n_days_ago = now - datetime.timedelta(days=past_days)
        data_filters.update({"ctime": {'>=': n_days_ago}})

    qbl.append(datatype, tag="data", with_user="creator", filters=data_filters, project=project)

    # If there is a group restriction
    if group_pks is not None:
        group_filters = dict()
        group_filters.update({"id": {"in": group_pks}})
        qbl.append(orm.Group, tag="group", filters=group_filters, with_node="data")

    qbl.order_by({datatype: {'ctime': 'asc'}})

    object_list = qbl.distinct()
    return object_list.all()


# pylint: disable=unused-argument,too-many-arguments
def data_list(datatype, columns, elements, elements_only, formula_mode, past_days, groups, all_users):
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
