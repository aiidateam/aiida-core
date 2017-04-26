# -*- coding: utf8 -*-
"""
:py:mod:`click` parameter type for AiiDA computer nodes
"""
import click
from click_completion import startswith
from click_spinner import spinner as cli_spinner

from aiida.cmdline.aiida_verdi.verdic_utils import aiida_dbenv


class ComputerParam(click.ParamType):
    """
    :py:mod:`click` parameter type for arguments and options which are meant
    to recieve a valid code name or pk.

    Handles completion and conversion

    :param convert: should the argument be converted into a Computer node? default=True
    :param pass_pk: if convert is True: convert to pk
    """
    name = 'aiida computer'

    def __init__(self, convert=True, pass_pk=False, **kwargs):
        self.get_from_db = convert
        self.pass_pk = pass_pk

    @aiida_dbenv
    def convert(self, value, param, ctx):
        """
        tries to get a computer from the db (if convert=True).
        """
        computers = [i[0] for i in self.complete(ctx)]
        if not value:
            raise click.BadParameter('computer parameter cannot be empty')
        if value not in computers:
            raise click.BadParameter('{} is not a name or pk of a computer!'.format(value))
        '''try convert to int (pk)'''
        try:
            value = int(value)
        except ValueError:
            pass
        if self.get_from_db:
            from aiida.orm.computer import Computer
            '''get computer from db'''
            value = Computer.get(value)
        elif self.pass_pk:
            from aiida.orm.computer import Computer
            value = Computer.get(value).pk
        return value

    @aiida_dbenv
    def complete(self, ctx=None, incomplete=''):
        """
        list computer names and pks
        """
        with cli_spinner():
            from aiida.orm.querybuilder import QueryBuilder
            results = []
            qb = QueryBuilder()
            qb.append(type='computer', project=['name'])
            names = [i for j in qb.iterall() for i in j if startswith(i, incomplete)]
            results += [(i, None) for i in names]
            qb = QueryBuilder()
            qb.append(type='computer', project=['id', 'name'])
            results += [(str(i[0]), i[1]) for i in qb.iterall() if startswith(str(i[0]), incomplete)]
            return results

    def get_missing_message(self, param):
        """
        returns the message to be printed on :py:class:`click.MissingParameter`
        """
        comps = ['{:<12} {}'.format(*c) for c in self.complete()]
        return 'Possible arguments are:\n\n' + '\n'.join(comps)
