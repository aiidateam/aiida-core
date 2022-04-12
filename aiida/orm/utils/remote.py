# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for operations on files on remote computers."""
import os

from aiida.orm.nodes.data.remote.base import RemoteData


def clean_remote(transport, path):
    """
    Recursively remove a remote folder, with the given absolute path, and all its contents. The path should be
    made accessible through the transport channel, which should already be open

    :param transport: an open Transport channel
    :param path: an absolute path on the remote made available through the transport
    """
    if not isinstance(path, str):
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


def get_calcjob_remote_paths(  # pylint: disable=too-many-locals
    pks=None,
    past_days=None,
    older_than=None,
    computers=None,
    user=None,
    backend=None,
    exit_status=None,
    only_not_cleaned=False,
):
    """
    Return a mapping of computer uuids to a list of remote paths, for a given set of calcjobs. The set of
    calcjobs will be determined by a query with filters based on the pks, past_days, older_than,
    computers and user arguments.

    :param pks: only include calcjobs with a pk in this list
    :param past_days: only include calcjobs created since past_days
    :param older_than: only include calcjobs older than
    :param computers: only include calcjobs that were ran on these computers
    :param user: only include calcjobs of this user
    :param exit_status: only select calcjob with this exit_status
    :param only_not_cleaned: only include calcjobs whose workdir have not been cleaned
    :return: mapping of computer uuid and list of remote folder
    """
    from datetime import timedelta

    from aiida import orm
    from aiida.common import timezone
    from aiida.orm import CalcJobNode

    filters_calc = {}
    filters_computer = {}
    filters_remote = {}

    if user is None:
        user = orm.User.collection.get_default()

    if computers is not None:
        filters_computer['id'] = {'in': [computer.pk for computer in computers]}

    if past_days is not None:
        filters_calc['mtime'] = {'>': timezone.now() - timedelta(days=past_days)}

    if older_than is not None:
        older_filter = {'<': timezone.now() - timedelta(days=older_than)}
        # Check if we need to apply the AND condition
        if 'mtime' not in filters_calc:
            filters_calc['mtime'] = older_filter
        else:
            past_filter = filters_calc['mtime']
            filters_calc['mtime'] = {'and': [past_filter, older_filter]}

    if exit_status is not None:
        filters_calc['attributes.exit_status'] = exit_status

    if pks:
        filters_calc['id'] = {'in': pks}

    if only_not_cleaned is True:
        filters_remote['or'] = [{
            f'extras.{RemoteData.KEY_EXTRA_CLEANED}': {
                '!==': True
            }
        }, {
            'extras': {
                '!has_key': RemoteData.KEY_EXTRA_CLEANED
            }
        }]

    query = orm.QueryBuilder(backend=backend)
    query.append(CalcJobNode, tag='calc', filters=filters_calc)
    query.append(
        RemoteData, tag='remote', project=['*'], edge_filters={'label': 'remote_folder'}, filters=filters_remote
    )
    query.append(orm.Computer, with_node='calc', tag='computer', project=['uuid'], filters=filters_computer)
    query.append(orm.User, with_node='calc', filters={'email': user.email})

    if query.count() == 0:
        return None

    path_mapping = {}

    for remote_data, computer_uuid in query.all():
        path_mapping.setdefault(computer_uuid, []).append(remote_data)

    return path_mapping
