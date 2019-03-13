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

from contextlib import contextmanager

from aiida.backends.general.abstractqueries import AbstractQueryManager


class SqlaQueryManager(AbstractQueryManager):
    """
    SQLAlchemy implementation of custom queries, for efficiency reasons
    """

    def __init__(self, backend):
        super(SqlaQueryManager, self).__init__(backend)

    def get_creation_statistics(
            self,
            user_pk=None
    ):
        """
        Return a dictionary with the statistics of node creation, summarized by day,
        optimized for the Django backend.

        :note: Days when no nodes were created are not present in the returned `ctime_by_day` dictionary.

        :param user_pk: If None (default), return statistics for all users.
            If user pk is specified, return only the statistics for the given user.

        :return: a dictionary as
            follows::

                {
                   "total": TOTAL_NUM_OF_NODES,
                   "types": {TYPESTRING1: count, TYPESTRING2: count, ...},
                   "ctime_by_day": {'YYYY-MMM-DD': count, ...}

            where in `ctime_by_day` the key is a string in the format 'YYYY-MM-DD' and the value is
            an integer with the number of nodes created that day.
        """
        import sqlalchemy as sa
        import aiida.backends.sqlalchemy
        from aiida.backends.sqlalchemy import models as m

        # Get the session (uses internally aldjemy - so, sqlalchemy) also for the Djsite backend
        s = aiida.backends.sqlalchemy.get_scoped_session()

        retdict = {}

        total_query = s.query(m.node.DbNode)
        types_query = s.query(m.node.DbNode.node_type.label('typestring'),
                              sa.func.count(m.node.DbNode.id))
        stat_query = s.query(sa.func.date_trunc('day', m.node.DbNode.ctime).label('cday'),
                             sa.func.count(m.node.DbNode.id))

        if user_pk is not None:
            total_query = total_query.filter(m.node.DbNode.user_id == user_pk)
            types_query = types_query.filter(m.node.DbNode.user_id == user_pk)
            stat_query = stat_query.filter(m.node.DbNode.user_id == user_pk)

        # Total number of nodes
        retdict["total"] = total_query.count()

        # Nodes per type
        retdict["types"] = dict(types_query.group_by('typestring').all())

        # Nodes created per day
        stat = stat_query.group_by('cday').order_by('cday').all()

        ctime_by_day = {_[0].strftime('%Y-%m-%d'): _[1] for _ in stat}
        retdict["ctime_by_day"] = ctime_by_day

        return retdict
        # Still not containing all dates
