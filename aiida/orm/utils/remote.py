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


def get_calcjob_remote_paths(pks=None, past_days=None, older_than=None, computers=None, user=None):
    """
    Return a mapping of computer uuids to a list of remote paths, for a given set of calcjobs. The set of
    calcjobs will be determined by a query with filters based on the pks, past_days, older_than,
    computers and user arguments.

    :param pks: onlu include calcjobs with a pk in this list
    :param past_days: only include calcjobs created since past_days
    :param older_than: only include calcjobs older than
    :param computers: only include calcjobs that were ran on these computers
    :param user: only include calcjobs of this user
    :return: mapping of computer uuid and list of remote paths, or None
    """
    from datetime import timedelta

    from aiida import orm
    from aiida.orm import CalcJobNode
    from aiida.common import timezone

    filters_calc = {}
    filters_computer = {}

    if user is None:
        user = orm.User.objects.get_default()

    if computers is not None:
        filters_computer['id'] = {'in': [computer.pk for computer in computers]}

    if past_days is not None:
        filters_calc['mtime'] = {'>': timezone.now() - timedelta(days=past_days)}

    if older_than is not None:
        filters_calc['mtime'] = {'<': timezone.now() - timedelta(days=older_than)}

    if pks:
        filters_calc['id'] = {'in': pks}

    qb = orm.QueryBuilder()
    qb.append(CalcJobNode, tag='calc', project=['attributes.remote_workdir'], filters=filters_calc)
    qb.append(orm.Computer, with_node='calc', tag='computer', project=['*'], filters=filters_computer)
    qb.append(orm.User, with_node='calc', filters={'email': user.email})

    if qb.count() == 0:
        return None

    path_mapping = {}

    for path, computer in qb.all():
        if path is not None:
            path_mapping.setdefault(computer.uuid, []).append(path)

    return path_mapping
