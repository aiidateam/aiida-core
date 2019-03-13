# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backup implementation for SqlAlchemy backend."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import os

import aiida.backends.sqlalchemy
from aiida.backends.sqlalchemy.models.node import DbNode
from aiida.manage.backup.backup_base import AbstractBackup, BackupError
from aiida.common.folders import RepositoryFolder
from aiida.orm.utils.repository import Repository


class Backup(AbstractBackup):
    """
    Backup for sqlalchemy backend
    """
    _batch_size = 50

    def _query_first_node(self):
        """
        Query first node
        :return:
        """
        res = aiida.backends.sqlalchemy.get_scoped_session().query(DbNode).order_by(DbNode.ctime).first()

        if res is None:
            return list()

        return [res]

    def _get_query_set_length(self, query_set):
        """
        Get query set length
        """
        return query_set.count()

    def _get_query_sets(self, start_of_backup, backup_end_for_this_round):
        """
        Get Nodes and Worflows query set from start to en

        d of backup.
        :param start_of_backup:
        :param backup_end_for_this_round:
        :return:
        """
        q_nodes = aiida.backends.sqlalchemy.get_scoped_session().query(DbNode).filter(
            DbNode.mtime >= start_of_backup).filter(DbNode.mtime <= backup_end_for_this_round)

        return [q_nodes]

    def _get_query_set_iterator(self, query_set):
        """
        Get query set iterator
        :param query_set:
        :return:
        """
        return query_set.yield_per(self._batch_size)

    def _get_source_directory(self, item):
        """

        :param item:
        :return:
        """
        # pylint: disable=protected-access
        if isinstance(item, DbNode):
            source_dir = os.path.normpath(RepositoryFolder(section=Repository._section_name, uuid=item.uuid).abspath)
        else:
            # Raise exception
            self._logger.error("Unexpected item type to backup: %s", type(item))
            raise BackupError("Unexpected item type to backup: {}".format(type(item)))
        return source_dir
