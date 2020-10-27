# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Manage AiiDA queries."""
import abc


class AbstractQueryManager(abc.ABC):
    """Manage AiiDA queries."""

    def __init__(self, backend):
        """
        :param backend: The AiiDA backend
        :type backend: :class:`aiida.orm.implementation.sql.backends.SqlBackend`
        """
        self._backend = backend

    def get_duplicate_uuids(self, table):
        """
        Return a list of rows with identical UUID

        :param table: Database table with uuid column, e.g. 'db_dbnode'
        :type str:

        :return: list of tuples of (id, uuid) of rows with duplicate UUIDs
        :rtype list:
        """
        query = f"""
            SELECT s.id, s.uuid FROM (SELECT *, COUNT(*) OVER(PARTITION BY uuid) AS c FROM {table})
            AS s WHERE c > 1
            """
        return self._backend.execute_raw(query)

    def apply_new_uuid_mapping(self, table, mapping):
        for pk, uuid in mapping.items():
            query = f"""UPDATE {table} SET uuid = '{uuid}' WHERE id = {pk}"""
            with self._backend.cursor() as cursor:
                cursor.execute(query)

    @staticmethod
    def get_creation_statistics(user_pk=None):
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
        import datetime
        from collections import Counter
        from aiida.orm import User, Node, QueryBuilder

        def count_statistics(dataset):

            def get_statistics_dict(dataset):
                results = {}
                for count, typestring in sorted((v, k) for k, v in dataset.items())[::-1]:
                    results[typestring] = count
                return results

            count_dict = {}

            types = Counter([r[2] for r in dataset])
            count_dict['types'] = get_statistics_dict(types)

            ctimelist = [r[1].strftime('%Y-%m-%d') for r in dataset]
            ctime = Counter(ctimelist)

            if ctimelist:

                # For the way the string is formatted, we can just sort it alphabetically
                firstdate = datetime.datetime.strptime(sorted(ctimelist)[0], '%Y-%m-%d')
                lastdate = datetime.datetime.strptime(sorted(ctimelist)[-1], '%Y-%m-%d')

                curdate = firstdate
                outdata = {}

                while curdate <= lastdate:
                    curdatestring = curdate.strftime('%Y-%m-%d')
                    outdata[curdatestring] = ctime.get(curdatestring, 0)
                    curdate += datetime.timedelta(days=1)
                count_dict['ctime_by_day'] = outdata

            else:
                count_dict['ctime_by_day'] = {}

            return count_dict

        statistics = {}

        q_build = QueryBuilder()
        q_build.append(Node, project=['id', 'ctime', 'type'], tag='node')

        if user_pk is not None:
            q_build.append(User, with_node='node', project='email', filters={'pk': user_pk})
        qb_res = q_build.all()

        # total count
        statistics['total'] = len(qb_res)
        statistics.update(count_statistics(qb_res))

        return statistics

    @staticmethod
    def _extract_formula(akinds, asites, args):
        """
        Extract formula from the structure object.

        :param akinds: list of kinds, e.g. [{'mass': 55.845, 'name': 'Fe', 'symbols': ['Fe'], 'weights': [1.0]},
                                            {'mass': 15.9994, 'name': 'O', 'symbols': ['O'], 'weights': [1.0]}]
        :param asites: list of structure sites e.g. [{'position': [0.0, 0.0, 0.0], 'kind_name': 'Fe'},
                                                        {'position': [2.0, 2.0, 2.0], 'kind_name': 'O'}]
        :param args: a namespace with parsed command line parameters, here only 'element' and 'element_only' are used
        :type args: dict

        :return: a string with formula if the formula is found
        """
        from aiida.orm.nodes.data.structure import (get_formula, get_symbols_string)

        if args.element is not None:
            all_symbols = [_['symbols'][0] for _ in akinds]
            if not any([s in args.element for s in all_symbols]):
                return None

        if args.element_only is not None:
            all_symbols = [_['symbols'][0] for _ in akinds]
            if not all([s in all_symbols for s in args.element_only]):
                return None

        # We want only the StructureData that have attributes
        if akinds is None or asites is None:
            return '<<UNKNOWN>>'

        symbol_dict = {}
        for k in akinds:
            symbols = k['symbols']
            weights = k['weights']
            symbol_dict[k['name']] = get_symbols_string(symbols, weights)

        try:
            symbol_list = []
            for site in asites:
                symbol_list.append(symbol_dict[site['kind_name']])
            formula = get_formula(symbol_list, mode=args.formulamode)
        # If for some reason there is no kind with the name
        # referenced by the site
        except KeyError:
            formula = '<<UNKNOWN>>'
        return formula

    def get_bands_and_parents_structure(self, args):
        """Search for bands and return bands and the closest structure that is a parent of the instance.
        This is the backend independent way, can be overriden for performance reason

        :returns:
            A list of sublists, each latter containing (in order):
                pk as string, formula as string, creation date, bandsdata-label
        """
        # pylint: disable=too-many-locals

        import datetime
        from aiida.common import timezone
        from aiida import orm

        q_build = orm.QueryBuilder()
        if args.all_users is False:
            q_build.append(orm.User, tag='creator', filters={'email': orm.User.objects.get_default().email})
        else:
            q_build.append(orm.User, tag='creator')

        group_filters = {}

        if args.group_name is not None:
            group_filters.update({'name': {'in': args.group_name}})
        if args.group_pk is not None:
            group_filters.update({'id': {'in': args.group_pk}})

        q_build.append(orm.Group, tag='group', filters=group_filters, with_user='creator')

        bdata_filters = {}
        if args.past_days is not None:
            bdata_filters.update({'ctime': {'>=': timezone.now() - datetime.timedelta(days=args.past_days)}})

        q_build.append(
            orm.BandsData, tag='bdata', with_group='group', filters=bdata_filters, project=['id', 'label', 'ctime']
        )
        bands_list_data = q_build.all()

        q_build.append(
            orm.StructureData,
            tag='sdata',
            with_descendants='bdata',
            # We don't care about the creator of StructureData
            project=['id', 'attributes.kinds', 'attributes.sites']
        )

        q_build.order_by({orm.StructureData: {'ctime': 'desc'}})

        structure_dict = dict()
        list_data = q_build.distinct().all()
        for bid, _, _, _, akinds, asites in list_data:
            structure_dict[bid] = (akinds, asites)

        entry_list = []
        already_visited_bdata = set()

        for [bid, blabel, bdate] in bands_list_data:

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
            strct = structure_dict.get(bid, None)

            if strct is not None:
                akinds, asites = strct
                formula = self._extract_formula(akinds, asites, args)
            else:
                if args.element is not None or args.element_only is not None:
                    formula = None
                else:
                    formula = '<<NOT FOUND>>'

            if formula is None:
                continue
            entry_list.append([str(bid), str(formula), bdate.strftime('%d %b %Y'), blabel])

        return entry_list

    @staticmethod
    def get_all_parents(node_pks, return_values=('id',)):
        """Get all the parents of given nodes

        :param node_pks: one node pk or an iterable of node pks
        :return: a list of aiida objects with all the parents of the nodes"""
        from aiida.orm import Node, QueryBuilder

        q_build = QueryBuilder()
        q_build.append(Node, tag='low_node', filters={'id': {'in': node_pks}})
        q_build.append(Node, with_descendants='low_node', project=return_values)
        return q_build.all()
