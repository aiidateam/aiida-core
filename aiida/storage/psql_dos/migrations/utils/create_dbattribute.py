# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Create an old style node attribute/extra, via the `db_dbattribute`/`db_dbextra` tables.

Adapted from: `aiida/backends/djsite/db/migrations/__init__.py`
"""
from __future__ import annotations

import datetime
import json

from aiida.common.exceptions import ValidationError
from aiida.common.timezone import make_aware


def create_rows(key: str, value, node_id: int) -> list[dict]:  # pylint: disable=too-many-branches
    """Create an old style node attribute/extra, via the `db_dbattribute`/`db_dbextra` tables.

    :note: No hits are done on the DB, in particular no check is done
        on the existence of the given nodes.

    :param key: a string with the key to create (can contain the
        separator self._sep if this is a sub-attribute: indeed, this
        function calls itself recursively)
    :param value: the value to store (a basic data type or a list or a dict)
    :param node_id: the node id to store the attribute/extra

    :return: A list of column name -> value dictionaries, with which to instantiate database rows
    """
    list_to_return = []

    columns = {
        'key': key,
        'dbnode_id': node_id,
        'datatype': 'none',
        'tval': '',
        'bval': None,
        'ival': None,
        'fval': None,
        'dval': None,
    }

    if isinstance(value, bool):
        columns['datatype'] = 'bool'
        columns['bval'] = value

    elif isinstance(value, int):
        columns['datatype'] = 'int'
        columns['ival'] = value

    elif isinstance(value, float):
        columns['datatype'] = 'float'
        columns['fval'] = value
        columns['tval'] = ''

    elif isinstance(value, str):
        columns['datatype'] = 'txt'
        columns['tval'] = value

    elif isinstance(value, datetime.datetime):

        columns['datatype'] = 'date'
        columns['dval'] = make_aware(value)

    elif isinstance(value, (list, tuple)):

        columns['datatype'] = 'list'
        columns['ival'] = len(value)

        for i, subv in enumerate(value):
            # I do not need get_or_create here, because
            # above I deleted all children (and I
            # expect no concurrency)
            # NOTE: I do not pass other_attribs
            list_to_return.extend(create_rows(f'{key}.{i:d}', subv, node_id))

    elif isinstance(value, dict):

        columns['datatype'] = 'dict'
        columns['ival'] = len(value)

        for subk, subv in value.items():
            if not isinstance(key, str) or not key:
                raise ValidationError('The key must be a non-empty string.')
            if '.' in key:
                raise ValidationError(
                    "The separator symbol '.' cannot be present in the key of attributes, extras, etc."
                )
            list_to_return.extend(create_rows(f'{key}.{subk}', subv, node_id))
    else:
        try:
            jsondata = json.dumps(value)
        except TypeError:
            raise ValueError(
                f'Unable to store the value: it must be either a basic datatype, or json-serializable: {value}'
            ) from TypeError

        columns['datatype'] = 'json'
        columns['tval'] = jsondata

    # create attr row and add to list_to_return
    list_to_return.append(columns)

    return list_to_return
