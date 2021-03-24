# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" Resources for using grafana with the REST API """
from datetime import datetime


def deduce_mpiproc(data_dict):
    """Description"""
    data_resources = data_dict['resources']
    manual_calculation = ('num_mpiprocs_per_machine' in data_resources) and ('num_machines' in data_resources)
    ready_calculation = 'tot_num_mpiprocs' in data_resources

    mpiproc = 0

    if manual_calculation:
        np_per_node = data_resources['num_mpiprocs_per_machine']
        total_nodes = data_resources['num_machines']
        mpiproc = total_nodes * np_per_node

    if ready_calculation:
        mpiproc = data_resources['tot_num_mpiprocs']

    if 'last_job_info' in data_dict:
        mpiproc = data_dict['last_job_info']['num_mpiprocs']

    return mpiproc


def process_grafana_request(entry_point, request_dict):
    """Description"""
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    from aiida import orm

    if entry_point == 'search':
        #data = ['resource_usage', 'current_resource_usage']
        data = ['current_resource_usage']

    elif entry_point == 'query':
        time_i = datetime.strptime(request_dict['range']['from'], '%Y-%m-%dT%H:%M:%S.%fZ')
        time_f = datetime.strptime(request_dict['range']['to'], '%Y-%m-%dT%H:%M:%S.%fZ')
        #time_d = request_dict['intervalMs']
        target = request_dict['targets'][0]['target']

        if target == 'resource_usage':

            # Get intervals
            delta_t = (time_f - time_i) / 100
            interval_list = []
            for interval_n in range(100):
                time_ii = time_i + delta_t * interval_n
                time_ff = time_i + delta_t * (interval_n + 1)
                interval_list.append({'ti': time_ii, 'tf': time_ff})

            datapoints = []
            for interval in interval_list:
                qb0 = orm.QueryBuilder()
                qb0.append(
                    orm.CalcJobNode,
                    project=['attributes.resources', 'attributes.scheduler_lastchecktime'],
                    filters={'ctime': {
                        '<=': interval['tf']
                    }},
                )

                total_processors = 0
                for query_list in qb0.all():
                    query_data = query_list[0]
                    # 2016-03-03T03:46:03.811047+00:00
                    query_time = datetime.strptime(query_list[1][:-6], '%Y-%m-%dT%H:%M:%S.%f')

                    valid_time = query_time >= interval['ti']
                    manual_calculation = ('num_mpiprocs_per_machine' in query_data) and ('num_machines' in query_data)
                    ready_calculation = 'tot_num_mpiprocs' in query_data

                    if manual_calculation and valid_time:
                        np_per_node = query_data['num_mpiprocs_per_machine']
                        total_nodes = query_data['num_machines']
                        total_processors = total_processors + total_nodes * np_per_node

                    if ready_calculation and valid_time:
                        total_processors = total_processors + query_data['tot_num_mpiprocs']

                timepoint = (interval['tf'].timestamp() + interval['ti'].timestamp()) * 500
                datapoints.append([total_processors, timepoint])

            data = [{'target': 'total_mpiproc', 'datapoints': datapoints}]

        elif target == 'current_resource_usage':

            workflows_running = 0

            qb0 = orm.QueryBuilder()
            qb0.append(
                orm.ProcessNode,
                tag='all_current',
                filters={'attributes.process_state': {
                    'in': ['created', 'waiting', 'running']
                }},
            )
            set_all = {nodel[0].pk for nodel in qb0.all()}

            qb0.append(
                orm.ProcessNode,
                with_incoming='all_current',
                filters={'attributes.process_state': {
                    'in': ['created', 'waiting', 'running']
                }},
            )
            set_children = {nodel[0].pk for nodel in qb0.all()}

            set_parents = set_all - set_children
            workflows_running = len(set_parents)

            mpiproc_waiting = 0
            mpiproc_running = 0

            qb0 = orm.QueryBuilder()
            qb0.append(
                orm.CalcJobNode,
                filters={'attributes.process_state': {
                    'in': ['created', 'waiting', 'running']
                }},
            )

            for query_list in qb0.all():
                query_node = query_list[0]
                query_data = query_node.attributes

                if 'RUNNING' in query_data['process_status']:
                    mpiproc_running = mpiproc_running + deduce_mpiproc(query_data)

                else:
                    mpiproc_waiting = mpiproc_waiting + deduce_mpiproc(query_data)

            timepoint0 = int(time_f.timestamp() * 1000)
            data = [
                {
                    'target': 'workflows_running',
                    'datapoints': [[workflows_running, timepoint0]]
                },
                {
                    'target': 'mpiproc_running',
                    'datapoints': [[mpiproc_running, timepoint0]]
                },
                {
                    'target': 'mpiproc_waiting',
                    'datapoints': [[mpiproc_waiting, timepoint0]]
                },
            ]

    elif entry_point == 'annotations':
        data = ['annotations']

    return data
