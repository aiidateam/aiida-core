# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backup implementation for any backend (using the QueryBuilder)."""
# pylint: disable=no-member

import os

from aiida.orm import Node
from aiida.manage.backup.backup_base import AbstractBackup, BackupError
from aiida.common.folders import RepositoryFolder
from aiida.orm.utils.repository import Repository


class Backup(AbstractBackup):
    """Backup for any backend"""

    def _query_first_node(self):
        """Query first node
        :return: The first Node object (return specific subclass thereof).
        :rtype: :class:`~aiida.orm.nodes.node.Node`
        """
        return Node.objects.find(order_by='ctime')[:1]

    def _get_query_set_length(self, query_set):
        """Get query set length"""
        return query_set.count()

    def _get_query_sets(self, start_of_backup, backup_end_for_this_round):
        """Get Nodes and Worflows query set from start to end of backup.

        :param start_of_backup: datetime object with start datetime of Node modification times for backup.
        :param backup_end_for_this_round: datetime object with end datetime of Node modification times for backup this
            round.

        :return: List of QueryBuilder queries/query.
        :rtype: :class:`~aiida.orm.querybuilder.QueryBuilder`
        """
        mtime_interval = {'mtime': {'and': [{'>=': str(start_of_backup)}, {'<=': str(backup_end_for_this_round)}]}}
        query_set = Node.objects.query()
        query_set.add_filter(Node, mtime_interval)

        return [query_set]

    def _get_query_set_iterator(self, query_set):
        """Get query set iterator

        :param query_set: QueryBuilder object
        :type query_set: :class:`~aiida.orm.querybuilder.QueryBuilder`

        :return: Generator, returning the results of the QueryBuilder query.
        :rtype: list

        :raises `~aiida.manage.backup.backup_base.BackupError`: if the number of yielded items in the list from
            iterall() is more than 1.
        """
        for item in query_set.iterall():
            yield_len = len(item)
            if yield_len == 1:
                yield item[0]
            else:
                msg = 'Unexpected number of items in list yielded from QueryBuilder.iterall(): %s'
                self._logger.error(msg, yield_len)
                raise BackupError(msg % yield_len)

    def _get_source_directory(self, item):
        """Retrieve the node repository folder

        :param item: Subclasses of Node.
        :type item: :class:`~aiida.orm.nodes.node.Node`

        :return: Normalized path to the Node's repository folder.
        :rtype: str
        """
        # pylint: disable=protected-access
        if isinstance(item, Node):
            source_dir = os.path.normpath(RepositoryFolder(section=Repository._section_name, uuid=item.uuid).abspath)
        else:
            # Raise exception
            msg = 'Unexpected item type to backup: %s'
            self._logger.error(msg, type(item))
            raise BackupError(msg % type(item))
        return source_dir
