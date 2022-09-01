# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility module with a factory of standard ``QueryBuilder`` instances for ``CalculationNodes``."""
from aiida.common.lang import classproperty

from .mapping import CalculationProjectionMapper


class CalculationQueryBuilder:
    """Utility class to construct a QueryBuilder instance for Calculation nodes and project the query set."""

    # This tuple serves to mark compound projections that cannot explicitly be projected in the QueryBuilder, but will
    # have to be manually projected from composing its individual projection constituents
    _compound_projections = ('state',)
    _default_projections = ('pk', 'ctime', 'process_label', 'state', 'process_status')
    _valid_projections = (
        'pk', 'uuid', 'ctime', 'mtime', 'state', 'process_state', 'process_status', 'exit_status', 'sealed',
        'process_label', 'label', 'description', 'node_type', 'paused', 'process_type', 'job_state', 'scheduler_state',
        'exception'
    )

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

    def get_filters(
        self,
        all_entries=False,
        process_state=None,
        process_label=None,
        paused=False,
        exit_status=None,
        failed=False,
        node_types=None
    ):
        """Return a set of QueryBuilder filters based on typical command line options.

        :param node_types: A tuple of node classes to filter for (must be sub classes of Calculation).
        :param all_entries: Boolean to negate filtering for process state.
        :param process_state: Filter for this process state attribute.
        :param process_label: Filter for this process label attribute.
        :param paused: Boolean, if True, filter for processes that are paused.
        :param exit_status: Filter for this exit status.
        :param failed: Boolean to filter only failed processes.
        :return: Dictionary of filters suitable for a QueryBuilder.append() call.
        """
        # pylint: disable=too-many-arguments
        from aiida.engine import ProcessState

        exit_status_attribute = self.mapper.get_attribute('exit_status')
        process_label_attribute = self.mapper.get_attribute('process_label')
        process_state_attribute = self.mapper.get_attribute('process_state')
        paused_attribute = self.mapper.get_attribute('paused')

        filters = {}

        if node_types is not None:
            filters['or'] = []
            for node_class in node_types:
                filters['or'].append({'type': node_class.class_node_type})

        if process_state and not all_entries:
            filters[process_state_attribute] = {'in': process_state}

        if process_label is not None:
            if '%' in process_label or '_' in process_label:
                filters[process_label_attribute] = {'like': process_label}
            else:
                filters[process_label_attribute] = process_label

        if paused:
            filters[paused_attribute] = True

        if failed:
            filters[process_state_attribute] = {'==': ProcessState.FINISHED.value}
            filters[exit_status_attribute] = {'>': 0}

        if exit_status is not None:
            filters[process_state_attribute] = {'==': ProcessState.FINISHED.value}
            filters[exit_status_attribute] = {'==': exit_status}

        return filters

    def get_query_set(self, relationships=None, filters=None, order_by=None, past_days=None, limit=None):
        """Return the query set of calculations for the given filters and query parameters.

        :param relationships: A mapping of relationships to join on, e.g. {'with_node': Group} to join on a Group. The
            keys in this dictionary should be the keyword used in the `append` method of the `QueryBuilder` to join the
            entity on that is defined as the value.
        :param filters: Rules to filter query results with.
        :param order_by: Order the query set by this criterion.
        :param past_days: Only include entries from the last past days.
        :param limit: Limit the query set to this number of entries.
        :return: The query set, a list of dictionaries.
        """
        import datetime

        from aiida import orm
        from aiida.common import timezone

        # Define the list of projections for the QueryBuilder, which are all valid minus the compound projections
        projected_attributes = [
            self.mapper.get_attribute(projection)
            for projection in self._valid_projections
            if projection not in self._compound_projections
        ]

        if filters is None:
            filters = {}

        if past_days is not None:
            filters['ctime'] = {'>': timezone.now() - datetime.timedelta(days=past_days)}

        builder = orm.QueryBuilder()
        builder.append(cls=orm.ProcessNode, filters=filters, project=projected_attributes, tag='process')

        if relationships is not None:
            for tag, entity in relationships.items():
                builder.append(cls=type(entity), filters={'id': entity.pk}, **{tag: 'process'})

        if order_by is not None:
            builder.order_by({'process': order_by})
        else:
            builder.order_by({'process': {'ctime': 'asc'}})

        if limit is not None:
            builder.limit(limit)

        return builder.iterdict()

    def get_projected(self, query_set, projections):
        """Project the query set for the given set of projections."""
        header = [self.mapper.get_label(projection) for projection in projections]
        result = [header]

        for query_result in query_set:
            result_row = [self.mapper.format(projection, query_result['process']) for projection in projections]
            result.append(result_row)

        return result
