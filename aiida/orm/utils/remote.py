# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import os
import six


def clean_remote(transport, path):
    """
    Recursively remove a remote folder, with the given absolute path, and all its contents. The path should be
    made accessible through the transport channel, which should already be open

    :param transport: an open Transport channel
    :param path: an absolute path on the remote made available through the transport
    """
    if not isinstance(path, six.string_types):
        raise ValueError('the path has to be a string type')

    if not os.path.isabs(path):
        raise ValueError('the path should be absolute')

    if not transport.is_open:
        raise ValueError('the transport should already be open')

    basedir, relative_path = os.path.split(path)

    try:
        transport.chdir(basedir)
        transport.rmtree(relative_path)
    except IOError:
        pass


def get_calculation_remote_paths(calculation_pks=None, past_days=None, older_than=None, computers=None, user=None):
    """
    Return a mapping of computer uuids to a list of remote paths, for a given set of calculations. The set of
    calculations will be determined by a query with filters based on the calculations_pks, past_days, older_than,
    computers and user arguments.

    :param calculations_pks: onlu include calculations with a pk in this list
    :param past_days: only include calculations created since past_days
    :param older_than: only include calculations older than
    :param computers: only include calculations that were ran on these computers
    :param user: only include calculations of this user
    :return: mapping of computer uuid and list of remote paths, or None
    """
    from datetime import timedelta

    from aiida.orm.backends import construct_backend
    from aiida.orm.computer import Computer as OrmComputer
    from aiida.orm.users import User as OrmUser
    from aiida.orm.calculation import Calculation as OrmCalculation
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.utils import timezone

    filters_calc = {}
    filters_computer = {}

    if user is None:
        backend = construct_backend()
        user = backend.users.get_default()

    if computers is not None:
        filters_computer['id'] = {'in': [computer.pk for computer in computers]}

    if past_days is not None:
        filters_calc['mtime'] = {'>': timezone.now() - timedelta(days=past_days)}

    if older_than is not None:
        filters_calc['mtime'] = {'<': timezone.now() - timedelta(days=older_than)}

    if calculation_pks:
        filters_calc['id'] = {'in': calculation_pks}

    qb = QueryBuilder()
    qb.append(OrmCalculation, tag='calc', project=['attributes.remote_workdir'], filters=filters_calc)
    qb.append(OrmComputer, computer_of='calc', tag='computer', project=['*'], filters=filters_computer)
    qb.append(OrmUser, creator_of='calc', filters={'email': user.email})

    if qb.count() == 0:
        return None

    path_mapping = {}

    for path, computer in qb.all():
        if path is not None:
            path_mapping.setdefault(computer.uuid, []).append(path)

    return path_mapping
