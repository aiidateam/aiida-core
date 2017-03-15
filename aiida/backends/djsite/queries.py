# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.backends.general.abstractqueries import AbstractQueryManager


class QueryManagerDjango(AbstractQueryManager):

    def query_jobcalculations_by_computer_user_state(
            self, state, computer=None, user=None,
            only_computer_user_pairs=False,
            only_enabled=True, limit=None):
        # Here I am overriding the implementation using the QueryBuilder:

        """
        Filter all calculations with a given state.

        Issue a warning if the state is not in the list of valid states.

        :param string state: The state to be used to filter (should be a string among
                those defined in aiida.common.datastructures.calc_states)
        :param computer: a Django DbComputer entry, or a Computer object, of a
                computer in the DbComputer table.
                A string for the hostname is also valid.
        :param user: a Django entry (or its pk) of a user in the DbUser table;
                if present, the results are restricted to calculations of that
                specific user
        :param bool only_computer_user_pairs: if False (default) return a queryset
                where each element is a suitable instance of Node (it should
                be an instance of Calculation, if everything goes right!)
                If True, return only a list of tuples, where each tuple is
                in the format
                ('dbcomputer__id', 'user__id')
                [where the IDs are the IDs of the respective tables]

        :return: a list of calculation objects matching the filters.
        """
        # I assume that calc_states are strings. If this changes in the future,
        # update the filter below from dbattributes__tval to the correct field.
        from aiida.orm import Computer,User
        from aiida.common.exceptions import InputValidationError
        from aiida.orm.implementation.django.calculation.job import JobCalculation
        from aiida.common.datastructures import calc_states
        from aiida.backends.djsite.db.models import DbUser

        if state not in calc_states:
            raise InputValidationError("querying for calculation state='{}', but it "
                                "is not a valid calculation state".format(state))



        kwargs = {}
        if computer is not None:
            # I convert it from various type of inputs
            # (string, DbComputer, Computer)
            # to a DbComputer type
            kwargs['dbcomputer'] = Computer.get(computer).dbcomputer
        if user is not None:
            kwargs['user'] = user
        if only_enabled:
            kwargs['dbcomputer__enabled'] = True


        queryresults = JobCalculation.query(
            dbattributes__key='state',
            dbattributes__tval=state,
            **kwargs)

        if only_computer_user_pairs:
            computer_users_ids = queryresults.values_list(
                'dbcomputer__id', 'user__id').distinct()
            computer_users = []
            for computer_id,  user_id in computer_users_ids: #return cls(dbcomputer=DbComputer.get_dbcomputer(computer))DbNode.objects.get(pk=pk).get_aiida_class()
                computer_users.append((Computer.get(computer_id), DbUser.objects.get(pk=user_id).get_aiida_class()))
            return computer_users

        elif limit is not None:
            return queryresults[:limit]
        else:
            return queryresults
