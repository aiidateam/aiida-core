# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A utility module with a factory of standard QueryBuilder instances for Calculation nodes."""
from __future__ import absolute_import
from aiida.common.utils import classproperty
from aiida.cmdline.utils.query.mapping import CalculationProjectionMapper


class CalculationQueryBuilder(object):
    """Utility class to construct a QueryBuilder instance for Calculation nodes and project the query set."""

    _default_projections = ('pk', 'ctime', 'state', 'process_label', 'process_status')
    _valid_projections = ('pk', 'uuid', 'ctime', 'mtime', 'state', 'process_state', 'process_status', 'exit_status',
                          'sealed', 'process_label', 'label', 'description', 'type', 'paused', 'process_type')

    def __init__(self, mapper=None):
        if mapper is None:
            self._mapper = CalculationProjectionMapper(self._valid_projections)
        else:
            self._mapper = mapper

    @property
    def mapper(self):
        return self._mapper

    @classproperty
    def default_projections(self):
        return self._default_projections

    @classproperty
    def valid_projections(self):
        return self._valid_projections

    def get_filters(self, all_entries=False, process_state=None, exit_status=None, failed=False, node_types=None):
        """
        Return a set of QueryBuilder filters based on typical command line options.

        :param node_types: a tuple of node classes to filter for (must be sub classes of Calculation)
        :param all_entries: boolean to negate filtering for process state
        :param process_state: filter for this process state
        :param exit_status: filter for this exit status
        :param failed: boolean to filter only failed processes
        :return: dictionary of filters suitable for a QueryBuilder.append() call
        """
        from aiida.work import ProcessState

        exit_status_attribute = self.mapper.get_attribute('exit_status')
        process_state_attribute = self.mapper.get_attribute('process_state')

        filters = {}

        if node_types is not None:
            filters['or'] = []
            for node_type in node_types:
                filters['or'].append({'type': node_type.plugin_type_string})

        if process_state and not all_entries:
            filters[process_state_attribute] = {'in': process_state}

        if failed:
            filters[process_state_attribute] = {'==': ProcessState.FINISHED.value}
            filters[exit_status_attribute] = {'>': 0}

        if exit_status is not None:
            filters[process_state_attribute] = {'==': ProcessState.FINISHED.value}
            filters[exit_status_attribute] = {'==': exit_status}

        return filters

    def get_query_set(self, filters=None, order_by=None, past_days=None, limit=None):
        """
        Return the query set of calculations for the given filters and query parameters

        :param filters: rules to filter query results with
        :param order_by: order the query set by this criterion
        :param past_days: only include entries from the last past days
        :param limit: limit the query set to this number of entries
        :return: the query set, a list of dictionaries
        """
        import datetime

        from aiida.orm.calculation import Calculation
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.utils import timezone

        projected_attributes = [self.mapper.get_attribute(projection) for projection in self._valid_projections]

        if filters is None:
            filters = {}

        if past_days is not None:
            filters['ctime'] = {'>': timezone.now() - datetime.timedelta(days=past_days)}

        builder = QueryBuilder()
        builder.append(cls=Calculation, filters=filters, project=projected_attributes, tag='calculation')

        if order_by is not None:
            builder.order_by({'calculation': order_by})
        else:
            builder.order_by({'calculation': {'ctime': 'asc'}})

        if limit is not None:
            builder.limit(limit)

        return builder.iterdict()

    def get_projected(self, query_set, projections):
        """
        Project the query set for the given set of projections
        """
        header = [self.mapper.get_label(projection) for projection in projections]
        result = [header]

        for query_result in query_set:
            result_row = [self.mapper.format(projection, query_result['calculation']) for projection in projections]
            result.append(result_row)

        return result
