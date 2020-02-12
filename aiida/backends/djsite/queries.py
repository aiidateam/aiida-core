# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Django query backend."""

# pylint: disable=import-error,no-name-in-module
from aiida.backends.general.abstractqueries import AbstractQueryManager


class DjangoQueryManager(AbstractQueryManager):
    """Object that mananges the Django queries."""

    def get_creation_statistics(self, user_pk=None):
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
            an integer with the number of nodes created that day."""
        # pylint: disable=no-member
        import sqlalchemy as sa
        import aiida.backends.djsite.db.models as djmodels
        from aiida.manage.manager import get_manager
        backend = get_manager().get_backend()

        # Get the session (uses internally aldjemy - so, sqlalchemy) also for the Djsite backend
        session = backend.get_session()

        retdict = {}

        total_query = session.query(djmodels.DbNode.sa)
        types_query = session.query(
            djmodels.DbNode.sa.node_type.label('typestring'), sa.func.count(djmodels.DbNode.sa.id)
        )
        stat_query = session.query(
            sa.func.date_trunc('day', djmodels.DbNode.sa.ctime).label('cday'), sa.func.count(djmodels.DbNode.sa.id)
        )

        if user_pk is not None:
            total_query = total_query.filter(djmodels.DbNode.sa.user_id == user_pk)
            types_query = types_query.filter(djmodels.DbNode.sa.user_id == user_pk)
            stat_query = stat_query.filter(djmodels.DbNode.sa.user_id == user_pk)

        # Total number of nodes
        retdict['total'] = total_query.count()

        # Nodes per type
        retdict['types'] = dict(types_query.group_by('typestring').all())

        # Nodes created per day
        stat = stat_query.group_by('cday').order_by('cday').all()

        ctime_by_day = {_[0].strftime('%Y-%m-%d'): _[1] for _ in stat}
        retdict['ctime_by_day'] = ctime_by_day

        return retdict
        # Still not containing all dates
        # temporary fix only for DJANGO backend
        # Will be useless when the _join_ancestors method of the QueryBuilder
        # will be re-implemented without using the DbPath

    @staticmethod
    def query_past_days(q_object, args):
        """
        Subselect to filter data nodes by their age.

        :param q_object: a query object
        :param args: a namespace with parsed command line parameters.
        """
        from aiida.common import timezone
        from django.db.models import Q
        import datetime
        if args.past_days is not None:
            now = timezone.now()
            n_days_ago = now - datetime.timedelta(days=args.past_days)
            q_object.add(Q(ctime__gte=n_days_ago), Q.AND)

    @staticmethod
    def query_group(q_object, args):
        """
        Subselect to filter data nodes by their group.

        :param q_object: a query object
        :param args: a namespace with parsed command line parameters.
        """
        from django.db.models import Q
        if args.group_name is not None:
            q_object.add(Q(dbgroups__name__in=args.group_name), Q.AND)
        if args.group_pk is not None:
            q_object.add(Q(dbgroups__pk__in=args.group_pk), Q.AND)

    @staticmethod
    def _extract_formula(struc_pk, args, deser_data):
        """Extract formula."""
        from aiida.orm.nodes.data.structure import (get_formula, get_symbols_string)

        if struc_pk is not None:
            # Exclude structures by the elements
            if args.element is not None:
                all_kinds = [k['symbols'] for k in deser_data[struc_pk]['kinds']]
                all_symbols = [item for sublist in all_kinds for item in sublist]
                if not any([s in args.element for s in all_symbols]):
                    return None
            if args.element_only is not None:
                all_kinds = [k['symbols'] for k in deser_data[struc_pk]['kinds']]
                all_symbols = [item for sublist in all_kinds for item in sublist]
                if not all([s in all_symbols for s in args.element_only]):
                    return None

            # build the formula
            symbol_dict = {
                k['name']: get_symbols_string(k['symbols'], k['weights']) for k in deser_data[struc_pk]['kinds']
            }
            try:
                symbol_list = [symbol_dict[s['kind_name']] for s in deser_data[struc_pk]['sites']]
                formula = get_formula(symbol_list, mode=args.formulamode)
            # If for some reason there is no kind with the name
            # referenced by the site
            except KeyError:
                formula = '<<UNKNOWN>>'
                # cycle if we imposed the filter on elements
                if args.element is not None or args.element_only is not None:
                    return None
        else:
            formula = '<<UNKNOWN>>'

        return formula

    def get_bands_and_parents_structure(self, args):
        """Returns bands and closest parent structure."""
        from django.db.models import Q
        from aiida.backends.djsite.db import models
        from aiida.common.utils import grouper
        from aiida.orm import BandsData

        q_object = None
        if args.all_users is False:
            from aiida import orm
            q_object = Q(user__id=orm.User.objects.get_default().id)
        else:
            q_object = Q()

        self.query_past_days(q_object, args)
        self.query_group(q_object, args)

        bands_list_data = models.DbNode.objects.filter(
            node_type__startswith=BandsData.class_node_type
        ).filter(q_object).distinct().order_by('ctime').values_list('pk', 'label', 'ctime')

        entry_list = []
        # the frist argument of the grouper function is the query group size.
        for this_chunk in grouper(100, [(_[0], _[1], _[2]) for _ in bands_list_data]):
            # gather all banddata pks
            pks = [_[0] for _ in this_chunk]

            # get the closest structures (WITHOUT DbPath)
            structure_dict = get_closest_parents(pks, Q(node_type='data.structure.StructureData.'), chunk_size=1)

            struc_pks = [structure_dict[pk] for pk in pks]

            # query for the attributes needed for the structure formula
            res_attr = models.DbNode.objects.filter(id__in=struc_pks).values_list('id', 'attributes')

            # prepare the printout
            for (b_id_lbl_date, struc_pk) in zip(this_chunk, struc_pks):
                formula = self._extract_formula(struc_pk, args, {rattr[0]: rattr[1] for rattr in res_attr})
                if formula is None:
                    continue
                entry_list.append([
                    str(b_id_lbl_date[0]),
                    str(formula), b_id_lbl_date[2].strftime('%d %b %Y'), b_id_lbl_date[1]
                ])

        return entry_list


def get_closest_parents(pks, *args, **kwargs):
    """Get the closest parents dbnodes of a set of nodes.

    :param pks: one pk or an iterable of pks of nodes
    :param chunk_size: we chunk the pks into groups of this size,
        to optimize the speed (default=50)
    :param print_progress: print the the progression if True (default=False).
    :param args: additional query parameters
    :param kwargs: additional query parameters
    :returns: a dictionary of the form
        pk1: pk of closest parent of node with pk1,
        pk2: pk of closest parent of node with pk2

    .. note:: It works also if pks is a list of nodes rather than their pks

    .. todo:: find a way to always get a parent (when there is one) from each pk.
        Now, when the same parent has several children in pks, only
        one of them is kept. This is a BUG, related to the use of a dictionary
        (children_dict, see below...).
        For now a work around is to use chunk_size=1."""

    from copy import deepcopy
    from aiida.backends.djsite.db import models
    from aiida.common.utils import grouper

    chunk_size = kwargs.pop('chunk_size', 50)
    print_progress = kwargs.pop('print_progress', False)

    result_dict = {}
    if print_progress:
        print('Chunk size:', chunk_size)

    for i, chunk_pks in enumerate(grouper(chunk_size, list(set(pks)) if isinstance(pks, list) else [pks])):
        if print_progress:
            print('Dealing with chunk #', i)
        result_chunk_dict = {}

        q_pks = models.DbNode.objects.filter(pk__in=chunk_pks).values_list('pk', flat=True)
        # Now I am looking for parents (depth=0) of the nodes in the chunk:

        q_inputs = models.DbNode.objects.filter(outputs__pk__in=q_pks).distinct()
        depth = -1  # to be consistent with the DbPath depth (=0 for direct inputs)
        children_dict = {k: v for k, v in q_inputs.values_list('pk', 'outputs__pk') if v in q_pks}
        # While I haven't found a closest ancestor for every member of chunk_pks:
        while q_inputs.count() > 0 and len(result_chunk_dict) < len(chunk_pks):
            depth += 1
            q_inp_filtered = q_inputs.filter(*args, **kwargs)
            if q_inp_filtered.count() > 0:
                result_chunk_dict.update({(children_dict[k], k)
                                          for k in q_inp_filtered.values_list('pk', flat=True)
                                          if children_dict[k] not in result_chunk_dict})
            inputs = list(q_inputs.values_list('pk', flat=True))
            q_inputs = models.DbNode.objects.filter(outputs__pk__in=inputs).distinct()

            q_inputs_dict = {k: children_dict[v] for k, v in q_inputs.values_list('pk', 'outputs__pk') if v in inputs}
            children_dict = deepcopy(q_inputs_dict)

        result_dict.update(result_chunk_dict)

    return result_dict
