# -*- coding: utf-8 -*-
"""
Node Parameter type for arguments and options
"""
import click
from click_completion import startswith
from click_spinner import spinner as cli_spinner

from aiida.cmdline.aiida_verdi.verdic_utils import aiida_dbenv


class NodeParam(click.ParamType):
    """
    :py:mod:`click` parameter type for Node nodes

    also serves as base class for other node type parameters

    if convert=True, passes a Node,
    if convert=False, passes the uuid of the Node
    if convert=False, pass_pk=True, passes the pk of the Node
    """
    name = 'aiida node'

    @property
    @aiida_dbenv
    def node_type(self):
        from aiida.orm import Node
        return Node

    def __init__(self, convert=True, pass_pk=False, **kwargs):
        self.get_from_db = convert
        self.pass_pk = pass_pk

    @aiida_dbenv
    def convert(self, value, param, ctx):
        """
        tries to load a Node from the given pk / uuid.

        returns the node or the uuid for convert=True / convert=False

        catches

        * empty arguments
        * no node for given pk / uuid
        * node is not the right type
        """
        from aiida.cmdline import delayed_load_node as load_node
        from aiida.common.exceptions import NotExistent

        if not value:
            raise click.BadParameter('computer parameter cannot be empty')

        try:
            '''assume is pk'''
            value = int(value)
            if value < 1:
                raise click.BadParameter("PK values start from 1")
            input_type='ID'
        except ValueError:
            '''assume is uuid'''
            pass
            input_type='UUID'

        '''try to load a node'''
        try:
            node = load_node(value)
        except NotExistent:
            '''no node found'''
            raise click.BadParameter("No node exists with {}={}.".format(input_type, value))

        '''ensure node is the right type'''
        if not isinstance(node, self.node_type):
            raise click.BadParameter("Node with ID={} is not of node_type; it is a {}".format(
                node.pk, node.__class__.__name__))

        if self.get_from_db:
            value = node
        else:
            if self.pass_pk:
                value = node.pk
            else:
                value = node.uuid
        return value

    @aiida_dbenv
    def complete(self, ctx=None, incomplete=''):
        """
        list node (pk with uuid and description)
        """
        with cli_spinner():
            from aiida.orm.querybuilder import QueryBuilder
            qb = QueryBuilder()
            qb.append(cls=self.node_type, project=['id', 'uuid', 'description', 'type'])
            '''init match list'''
            matching = []
            '''match against pk'''
            if not incomplete or incomplete.isdigit():
                matching = [i for i in qb.iterall() if str(i[0]).startswith(incomplete)]
                descstr = 'uuid = {node[1]}, type = {node[3]:<40} | {node[2]}'
                for m in matching:
                    m[3] = m[3].replace(self.node_type._query_type_string, '')
                results = [(str(i[0]), descstr.format(node=i)) for i in matching]
            '''if no matches from pk, match against uuid'''
            if not matching:
                matching = [i for i in qb.iterall() if  str(i[1]).startswith(incomplete)]
                descstr = 'pk = {node[0]}, type = {node[3]:<40} | {node[2]}'
                for m in matching:
                    m[3] = m[3].replace(self.node_type._query_type_string, '')
                results = [(str(i[1]), descstr.format(node=i)) for i in matching]
            '''take common part out of type string'''
            return results

    def get_missing_message(self, param):
        """
        returns the message to be printed on :py:class:`click.MissingParameter`
        """
        comps = ['{:<12} {}'.format(*c) for c in self.complete()]
        amount = len(comps)
        if amount > 10:
            comps = comps[:10]
            comps.append('... ({} more) ...'.format(amount - 10))

        return 'Possible arguments are:\n\n' + '\n'.join(comps)
