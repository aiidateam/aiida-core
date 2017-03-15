# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from collections import defaultdict
import datetime

from django.db.models import Q

from aiida.orm.implementation.general.querytool import AbstractQueryTool


from aiida.orm.implementation.django.node import Node

from aiida.utils.timezone import is_naive, make_aware, get_current_timezone




class QueryTool(AbstractQueryTool):

    def __init__(self):
        from warnings import warn
        warn("QueryTool is deprecated, use QueryBuilder instead", DeprecationWarning)
 
        self._class_string = None
        self._group_queries = []
        self._attr_queries = []
        self._attrs = {}
        self._extra_queries = []
        self._extras = {}
        self._pks_in = None

        self._queryobject = None

    def set_class(self, the_class):
        """
        Pass a class to filter results only of a specific Node (sub)class, and
        its subclasses.
        """
        # We are changing the query, clear the cache
        if not issubclass(the_class, Node):
            raise TypeError("You can only call this method on subclasses of Node, you are passing instead".format(
                the_class.__name__))
        self._queryobject = None
        self._class_string = the_class._query_type_string

    def set_group(self, group, exclude=False):
        """
        Filter calculations only within a given node.
        This can be called multiple times for an AND query.

        .. todo:: Add the possibility of specifying the group as an object
          rather than with its name, so that one can also query special groups,
          etc.

        .. todo:: Add the possibility of specifying "OR" type queries on
          multiple groups, and any combination of AND, OR, NOT.

        :param group: the name of the group
        :param exclude: if True, excude results
        """
        # # We are changing the query, clear the cache
        #        self._queryobject = None

        if isinstance(group, basestring):
            # BE CAREFUL! WE ALL TAKING ALL GROUPS,
            # IRREGARDLESS OF THE TYPE AND THE OWNER
            if exclude:
                self._group_queries.append(~Q(dbgroups__name=group))
            else:
                self._group_queries.append(Q(dbgroups__name=group))
        else:
            raise NotImplementedError("Still to implement passing a real group rather than its name")

    def limit_pks(self, pk_list):
        """
        Limit the query to a given list of pks.

        :param pk_list: the list of pks you want to limit your query to.
        """
        self._pks_in = [int(_) for _ in pk_list]

    def _get_query_object(self, order_by=None):
        from aiida.backends.djsite.db import models
        """
        Internal method that returns the Django query object that
        has been generated.

        :param order_by: If specified, is a string to order by.
        """
        if self._class_string is None:
            raise ValueError("You have to call set_class first.")

        if self._queryobject is None:
            res = models.DbNode.objects.filter(
                type__startswith=self._class_string)
            for group_qobj in self._group_queries:
                res = res.filter(group_qobj)
            if self._pks_in is not None:
                res = res.filter(pk__in=self._pks_in)
            for attr_qobj, reldata in self._attr_queries:
                if reldata:
                    if reldata['relation'] == '__input':
                        relationlink = "input_links"
                    elif reldata['relation'] == '__output':
                        relationlink = "output_links"
                    else:
                        raise ValueError("relation {} not implemented!".format(
                            reldata['relation']))
                    classinfo = {}
                    if reldata['nodeclass'] is not None:
                        classinfo['type__startswith'] = reldata['nodeclass']
                    linkedres = models.DbNode.objects.filter(
                        dbattributes__in=attr_qobj, **classinfo)
                    res = res.filter(**{
                        "{}{}__in".format(relationlink, reldata['relation']):
                            linkedres,
                        "{}__label".format(relationlink): reldata['linkname']})
                else:
                    res = res.filter(dbattributes__in=attr_qobj)
            for extra_qobj, reldata in self._extra_queries:
                if reldata:
                    if reldata['relation'] == '__input':
                        relationlink = "input_links"
                    elif reldata['relation'] == '__output':
                        relationlink = "output_links"
                    else:
                        raise ValueError("relation {} not implemented!".format(
                            reldata['relation']))
                    linkedres = models.DbNode.objects.filter(
                        dbextras__in=extra_qobj)
                    res = res.filter(**{
                        "{}{}__in".format(relationlink, reldata['relation']):
                            linkedres,
                        "{}__label".format(relationlink): reldata['linkname']})
                else:
                    res = res.filter(dbextras__in=extra_qobj)

            self._queryobject = res.distinct()

        if order_by is not None:
            self._queryobject = self._queryobject.order_by(order_by)

        return self._queryobject

    def get_attributes(self):
        """
        Get the raw values of all the attributes of the queried nodes.
        """
        from aiida.backends.djsite.db import models
        res = self._get_query_object()
        attrs = models.DbAttribute.objects.filter(
            dbnode__in=res).filter(key__in=self._attrs.keys()).values(
            'dbnode__pk', 'key', 'tval', 'dval',
            'ival', 'bval', 'fval', 'datatype')
        return attrs

    def _get_extras_raw(self):
        """
        Internal method to get the raw values of all the extras
        of the queried nodes.
        """
        from aiida.backends.djsite.db import models
        res = self._get_query_object()
        extras = models.DbExtra.objects.filter(
            dbnode__in=res).filter(key__in=self._extras.keys()).values(
            'dbnode__pk', 'key', 'tval', 'dval',
            'ival', 'bval', 'fval', 'datatype')
        return extras

    def _get_attrs_raw(self):
        """
        Internal method to get the raw values of all the attributes
        of the queried nodes.
        """
        from aiida.backends.djsite.db import models
        res = self._get_query_object()
        attrs = models.DbAttribute.objects.filter(
            dbnode__in=res).filter(key__in=self._attrs.keys()).values(
            'dbnode__pk', 'key', 'tval', 'dval',
            'ival', 'bval', 'fval', 'datatype')
        return attrs

    def run_query(self, with_data=False, order_by=None):
        """
        Run the query using the filters that have been pre-set on this
        class, and return a generator of the obtained Node (sub)classes.

        :param order_by: if specified, order by the given field
        """
        if with_data:
            attrs = self.create_attrs_dict()
            extras = self.create_extras_dict()

        for r in self._get_query_object(order_by=order_by):
            if with_data:
                yield r.get_aiida_class(), {'attrs': attrs.get(r.pk, {}),
                                            'extras': extras.get(r.pk, {})}
            else:
                yield r.get_aiida_class()

                # This can be useful, but risky
            #.prefetch_related('dbextras').prefetch_related('dbattributes'):
            #
            #            # Do we really want to do this?
            #        for r in res.distinct():
            #            yield r.get_aiida_class(), {
            #                'extras': self._create_extra_dict(r.dbextras.all()),
            #                'attrs': self._create_attr_dict(r.dbattributes.all())}
            #return res.distinct()

    def create_extras_dict(self):
        """
        Return a dictionary of the raw data from the
        extras associated to the queried nodes.
        """
        # TODO: implement lists and dicts
        field = {'txt': 'tval', 'float': 'fval', 'bool': 'bval',
                 'int': 'ival', 'date': 'dval', 'none': lambda x: None}
        relevant_extras = self._extras.keys()

        extrasdict = defaultdict(dict)

        for e in self._get_extras_raw():
            f = field[e['datatype']]
            if callable(f):
                extrasdict[e['dbnode__pk']][e['key']] = f(e)
            else:
                extrasdict[e['dbnode__pk']][e['key']] = e[f]

        return dict(extrasdict)

    def create_attrs_dict(self):
        """
        Return a dictionary of the raw data from the
        attributes associated to the queried nodes.
        """
        # TODO: implement lists and dicts
        field = {'txt': 'tval', 'float': 'fval', 'bool': 'bval',
                 'int': 'ival', 'date': 'dval', 'none': lambda x: None}
        relevant_attrs = self._attrs.keys()

        attrsdict = defaultdict(dict)

        for e in self._get_attrs_raw():
            f = field[e['datatype']]
            if callable(f):
                attrsdict[e['dbnode__pk']][e['key']] = f(e)
            else:
                attrsdict[e['dbnode__pk']][e['key']] = e[f]

        return dict(attrsdict)

    def add_attr_filter(self, key, filtername, value,
                        negate=False, relnode=None, relnodeclass=None):
        """
        Add a new filter on the value of attributes of the nodes you
        want to query.

        :param key: the value of the key
        :param filtername: the type of filter to apply. Multiple
          filters are supported (depending on the type of value),
          like '<=', '<', '>', '>=', '=', 'contains', 'iexact',
          'startswith', 'endswith', 'istartswith', 'iendswith', ...
          (the prefix 'i' means "case-insensitive", in the
          case of strings).
        :param value: the value of the attribute
        :param negate: if True, add the negation of the current filter
        :param relnode: if specified, asks to apply the filter not on
          the node that is currently being queried, but rather
          on a node linked to it.
          Can be "res" for output results, "inp.LINKNAME" for input nodes
          with a given link name, "out.LINKNAME" for output nodes
          with a given link name.
        :param relnodeclass: if relnode is specified, you can here add
          a further filter on the type of linked node for which you are
          executing the query (e.g., if you want to filter for outputs
          whose 'energy' value is lower than zero, but only if 'energy'
          is in a ParameterData node).
        """
        from aiida.backends.djsite.db import models
        return self._add_filter(key, filtername, value,
                                dbtable=models.DbAttribute,
                                negate=negate,
                                querieslist=self._attr_queries,
                                attrdict=self._attrs,
                                relnode=relnode, relnodeclass=relnodeclass)

    def add_extra_filter(self, key, filtername, value, negate=False, relnode=None, relnodeclass=None):
        """
        Add a new filter on the value of extras of the nodes you
        want to query.

        :param key: the value of the key
        :param filtername: the type of filter to apply. Multiple
          filters are supported (depending on the type of value),
          like '<=', '<', '>', '>=', '=', 'contains', 'iexact',
          'startswith', 'endswith', 'istartswith', 'iendswith', ...
          (the prefix 'i' means "case-insensitive", in the
          case of strings).
        :param value: the value of the extra
        :param negate: if True, add the negation of the current filter
        :param relnode: if specified, asks to apply the filter not on
          the node that is currently being queried, but rather
          on a node linked to it.
          Can be "res" for output results, "inp.LINKNAME" for input nodes
          with a given link name, "out.LINKNAME" for output nodes
          with a given link name.
        :param relnodeclass: if relnode is specified, you can here add
          a further filter on the type of linked node for which you are
          executing the query (e.g., if you want to filter for outputs
          whose 'energy' value is lower than zero, but only if 'energy'
          is in a ParameterData node).
        """
        from aiida.backends.djsite.db import models
        return self._add_filter(key, filtername, value,
                                dbtable=models.DbExtra,
                                negate=negate,
                                querieslist=self._extra_queries,
                                attrdict=self._extras,
                                relnode=relnode, relnodeclass=relnodeclass)

    def _add_filter(self, key, filtername, value, negate,
                    dbtable, querieslist, attrdict, relnode, relnodeclass):
        """
        Internal method to apply a filter either on Extras or Attributes,
        to avoid to repeat the same code in a DRY spirit.
        """
        valid_filters = {
            '': '',
            None: '',
            '=': '__exact',
            'exact': '__exact',
            'iexact': '__iexact',
            'contains': '__contains',
            'icontains': '__icontains',
            'startswith': '__startswith',
            'istartswith': '__istartswith',
            'endswith': '__endswith',
            'iendsswith': '__iendswith',
            '<': '__lt',
            'lt': '__lt',
            'lte': '__lte',
            'le': '__lte',
            '<=': '__lte',
            '>': '__gt',
            'gt': '__gt',
            'gte': '__gte',
            'ge': '__gte',
            '>=': '__gte',
        }

        querylist = []
        querydict = {}
        querydict['key'] = key

        try:
            internalfilter = valid_filters[filtername]
        except KeyError:
            raise ValueError("Filter '{}' is not a supported filter".format(
                filtername))

        if value is None:
            querydict['datatype'] = 'none'
        elif isinstance(value, bool):
            querydict['datatype'] = 'bool'
            if negate:
                querylist.append(~Q(**{
                    'bval{}'.format(internalfilter): value}))
            else:
                querydict['bval{}'.format(internalfilter)] = value
        elif isinstance(value, (int, long)):
            querydict['datatype'] = 'int'
            querydict['ival{}'.format(internalfilter)] = value
        elif isinstance(value, float):
            querydict['datatype'] = 'float'
            querydict['fval{}'.format(internalfilter)] = value
        elif isinstance(value, basestring):
            querydict['datatype'] = 'txt'
            if negate:
                querylist.append(~Q(**{
                    'tval{}'.format(internalfilter): value}))
            else:
                querydict['tval{}'.format(internalfilter)] = value
        elif isinstance(value, datetime.datetime):
            # current timezone is taken from the settings file of django
            if is_naive(value):
                value_aware = make_aware(value, get_current_timezone())
            else:
                value_aware = value
            querydict['datatype'] = 'date'
            querydict['dval{}'.format(internalfilter)] = value_aware
        # elif isinstance(value, list):
        #
        #    new_entry.datatype = 'list'
        #    new_entry.ival = length
        #elif isinstance(value, dict):
        #    new_entry.datatype = 'dict'
        #    new_entry.ival = len(value)
        else:
            raise TypeError("Only basic datatypes are supported in queries!")

        reldata = {}
        if relnode is not None:
            if (relnodeclass is not None and
                    not isinstance(relnodeclass, Node) and
                    not issubclass(relnodeclass, Node)):
                raise TypeError("relnodeclass must be an AiiDA node")
            if relnodeclass is None:
                reldata['nodeclass'] = None
            else:
                reldata['nodeclass'] = relnodeclass._query_type_string
            if relnode == 'res':
                reldata['relation'] = "__output"
                reldata['linkname'] = "output_parameters"
            elif relnode.startswith('out.'):
                reldata['relation'] = "__output"
                reldata['linkname'] = relnode[4:]
            elif relnode.startswith('inp.'):
                reldata['relation'] = "__input"
                reldata['linkname'] = relnode[4:]
            else:
                raise NotImplementedError("Implemented only for 'out.' and 'inp.' for the time being!")
        else:
            if relnodeclass is not None:
                raise ValueError("cannot pass relnodeclass if no relnode is specified")
        # We are changing the query, clear the cache
        self._queryobject = None
        querieslist.append((dbtable.objects.filter(
            *querylist, **querydict), reldata))
        if reldata:
            pass
        else:
            attrdict[key] = reldata

