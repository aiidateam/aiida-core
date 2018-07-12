# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from abc import ABCMeta, abstractmethod


class AbstractQueryManager(object):
    __metaclass__ = ABCMeta


    def __init__(self,  *args, **kwargs):
        pass


    # This is an example of a query that could be overriden by a better implementation,
    # for performance reasons:
    def query_jobcalculations_by_computer_user_state(
            self, state, computer=None, user=None,
            only_computer_user_pairs=False,
            only_enabled=True, limit=None
    ):
        """
        Filter all calculations with a given state.

        Issue a warning if the state is not in the list of valid states.

        :param state: The state to be used to filter (should be a string among
                those defined in aiida.common.datastructures.calc_states)
        :type state: str
        :param computer: a Django DbComputer entry, or a Computer object, of a
                computer in the DbComputer table.
                A string for the hostname is also valid.
        :param user: a Django entry (or its pk) of a user in the DbUser table;
                if present, the results are restricted to calculations of that
                specific user
        :param only_computer_user_pairs: if False (default) return a queryset
                where each element is a suitable instance of Node (it should
                be an instance of Calculation, if everything goes right!)
                If True, return only a list of tuples, where each tuple is
                in the format
                ('dbcomputer__id', 'user__id')
                [where the IDs are the IDs of the respective tables]
        :type only_computer_user_pairs: bool
        :param limit: Limit the number of rows returned
        :type limit: int

        :return: a list of calculation objects matching the filters.
        """
        # I assume that calc_states are strings. If this changes in the future,
        # update the filter below from dbattributes__tval to the correct field.
        from aiida.orm.computer import Computer
        from aiida.orm.calculation.job import JobCalculation
        from aiida.orm.user import User
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.common.exceptions import InputValidationError
        from aiida.common.datastructures import calc_states

        if state not in calc_states:
            raise InputValidationError("querying for calculation state='{}', but it "
                                "is not a valid calculation state".format(state))

        calcfilter = {'state': {'==': state}}
        computerfilter = {"enabled": {'==': True}}
        userfilter = {}

        if computer is None:
            pass
        elif isinstance(computer, int):
            computerfilter.update({'id': {'==': computer}})
        elif isinstance(computer, Computer):
            computerfilter.update({'id': {'==': computer.pk}})
        else:
            try:
                computerfilter.update({'id': {'==': computer.id}})
            except AttributeError as e:
                raise Exception(
                    "{} is not a valid computer\n{}".format(computer, e)
                )
        if user is None:
            pass
        elif isinstance(user, int):
            userfilter.update({'id': {'==': user}})
        else:
            try:
                userfilter.update({'id': {'==': int(user.id)}})
                # Is that safe?
            except:
                raise Exception("{} is not a valid user".format(user))

        qb = QueryBuilder()
        qb.append(type="computer", tag='computer', filters=computerfilter)
        qb.append(JobCalculation, filters=calcfilter, tag='calc', has_computer='computer')
        qb.append(type="user", tag='user', filters=userfilter,
                  creator_of="calc")

        if only_computer_user_pairs:
            qb.add_projection("computer", "*")
            qb.add_projection("user", "*")
            returnresult = qb.distinct().all()
        else:
            qb.add_projection("calc", "*")
            if limit is not None:
                qb.limit(limit)
            returnresult = qb.all()
            returnresult = zip(*returnresult)[0]
        return returnresult


    def get_creation_statistics(
            self,
            user_pk=None
    ):
        """
        Return a dictionary with the statistics of node creation, summarized by day.

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
        from aiida.orm.querybuilder import QueryBuilder as QB
        from aiida.orm import User, Node
        from collections import Counter
        import datetime

        def count_statistics(dataset):

            def get_statistics_dict(dataset):
                results = {}
                for count, typestring in sorted(
                        (v, k) for k, v in dataset.iteritems())[::-1]:
                    results[typestring] = count
                return results

            count_dict = {}

            types = Counter([r[2] for r in dataset])
            count_dict["types"] = get_statistics_dict(types)

            ctimelist = [r[1].strftime("%Y-%m-%d") for r in dataset]
            ctime = Counter(ctimelist)

            if len(ctimelist) > 0:

                # For the way the string is formatted, we can just sort it alphabetically
                firstdate = datetime.datetime.strptime(sorted(ctimelist)[0], '%Y-%m-%d')
                lastdate = datetime.datetime.strptime(sorted(ctimelist)[-1], '%Y-%m-%d')

                curdate = firstdate
                outdata = {}

                while curdate <= lastdate:
                    curdatestring = curdate.strftime('%Y-%m-%d')
                    outdata[curdatestring] = ctime.get(curdatestring, 0)
                    curdate += datetime.timedelta(days=1)
                count_dict["ctime_by_day"] = outdata

            else:
                count_dict["ctime_by_day"] = {}

            return count_dict

        statistics = {}

        q = QB()
        q.append(Node, project=['id', 'ctime', 'type'], tag='node')

        if user_pk is not None:
            q.append(User, creator_of='node', project='email', filters={'pk': user_pk})
        qb_res = q.all()

        # total count
        statistics["total"] = len(qb_res)
        statistics.update(count_statistics(qb_res))

        return statistics

    def get_bands_and_parents_structure(self, args):
        """
        Search for bands and return bands and the closest structure that is a parent of the instance.
        This is the backend independent way, can be overriden for performance reason

        :returns:
            A list of sublists, each latter containing (in order):
                pk as string, formula as string, creation date, bandsdata-label
        """
        
        import datetime
        from aiida.utils import timezone
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.backends.utils import get_automatic_user
        from aiida.orm.implementation import User
        from aiida.orm.implementation import Group
        from aiida.orm.data.structure import (get_formula, get_symbols_string)
        from aiida.orm.data.array.bands import BandsData
        from aiida.orm.data.structure import StructureData

        qb = QueryBuilder()
        if args.all_users is False:
            au = get_automatic_user()
            user = User(dbuser=au)
            qb.append(User, tag="creator", filters={"email": user.email})
        else:
            qb.append(User, tag="creator")

        bdata_filters = {}
        if args.past_days is not None:
            now = timezone.now()
            n_days_ago = now - datetime.timedelta(days=args.past_days)
            bdata_filters.update({"ctime": {'>=': n_days_ago}})

        qb.append(BandsData, tag="bdata", created_by="creator",
                  filters=bdata_filters,
                  project=["id", "label", "ctime"]
                  )

        group_filters = {}

        if args.group_name is not None:
            group_filters.update({"name": {"in": args.group_name}})
        if args.group_pk is not None:
            group_filters.update({"id": {"in": args.group_pk}})
        if group_filters:
            qb.append(Group, tag="group", filters=group_filters,
                      group_of="bdata")

        qb.append(StructureData, tag="sdata", ancestor_of="bdata",
                  # We don't care about the creator of StructureData
                  project=["id", "attributes.kinds", "attributes.sites"])

        qb.order_by({StructureData: {'ctime': 'desc'}})

        list_data = qb.distinct()

        entry_list = []
        already_visited_bdata = set()

        for [bid, blabel, bdate, sid, akinds, asites] in list_data.all():

            # We process only one StructureData per BandsData.
            # We want to process the closest StructureData to
            # every BandsData.
            # We hope that the StructureData with the latest
            # creation time is the closest one.
            # This will be updated when the QueryBuilder supports
            # order_by by the distance of two nodes.
            if already_visited_bdata.__contains__(bid):
                continue
            already_visited_bdata.add(bid)

            if args.element is not None:
                all_symbols = [_["symbols"][0] for _ in akinds]
                if not any([s in args.element for s in all_symbols]
                           ):
                    continue

            if args.element_only is not None:
                all_symbols = [_["symbols"][0] for _ in akinds]
                if not all(
                        [s in all_symbols for s in args.element_only]
                        ):
                    continue

            # We want only the StructureData that have attributes
            if akinds is None or asites is None:
                continue

            symbol_dict = {}
            for k in akinds:
                symbols = k['symbols']
                weights = k['weights']
                symbol_dict[k['name']] = get_symbols_string(symbols,
                                                            weights)

            try:
                symbol_list = []
                for s in asites:
                    symbol_list.append(symbol_dict[s['kind_name']])
                formula = get_formula(symbol_list,
                                      mode=args.formulamode)
            # If for some reason there is no kind with the name
            # referenced by the site
            except KeyError:
                formula = "<<UNKNOWN>>"
            entry_list.append([str(bid), str(formula),
                               bdate.strftime('%d %b %Y'), blabel])

        return entry_list

    def get_all_parents(self, node_pks, return_values=['id']):
        """
        Get all the parents of given nodes
        :param node_pks: one node pk or an iterable of node pks
        :return: a list of aiida objects with all the parents of the nodes
        """
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm import Node
        qb = QueryBuilder()
        qb.append(Node, tag='low_node',
                  filters={'id': {'in': node_pks}})
        qb.append(Node, ancestor_of='low_node', project=return_values)
        return qb.all()
