#-*- coding: utf8 -*-
"""
click parameter types for Codes
"""
import click
from click_completion import startswith
from click_spinner import spinner as cli_spinner

from aiida.cmdline.aiida_verdi.verdic_utils import aiida_dbenv
from aiida.cmdline.aiida_verdi.param_types.node import NodeParam


class CodeParam(NodeParam):
    """
    handle verification and tab-completion (relies on click-completion) for Code db entries
    """
    name = 'aiida code'

    @property
    @aiida_dbenv
    def node_type(self):
        from aiida.orm import Code
        return Code

    def get_possibilities(self, incomplete=''):
        """
        get all possible options for codes starting with incomplete

        :return: list of tuples with (name, help)
        """
        from aiida_verdi.verdic_utils import get_code_data
        names = [(c[1], c[2]) for c in get_code_data() if startswith(c[1], incomplete)]
        pks = [(str(c[0]), c[1]) for c in get_code_data() if startswith(str(c[0]), incomplete)]
        possibilities = names + pks
        return possibilities

    @aiida_dbenv
    def complete(self, ctx, incomplete):
        """
        load dbenv and run spinner while getting completions
        """
        with cli_spinner():
            suggestions = self.get_possibilities(incomplete=incomplete)
        return suggestions

    @aiida_dbenv
    def get_missing_message(self, param):
        with cli_spinner():
            code_item = '{:<12} {}'
            codes = [code_item.format(*p) for p in self.get_possibilities()]
        return 'Possible arguments are:\n\n' + '\n'.join(codes)

    @aiida_dbenv
    def convert(self, value, param, ctx):
        """
        check the given value corresponds to a code in the db, raise BadParam else

        gets the corresponding code object from the database for a pk or name
        and returns that
        """
        from aiida_verdi.verdic_utils import get_code
        codes = [c[0] for c in self.get_possibilities()]
        if value not in codes:
            raise click.BadParameter('Must be a code in you database', param=param)

        if self.get_from_db:
            value = get_code(value)
        elif self.pass_pk:
            value = get_code(value).pk
        else:
            value = get_code(value).uuid
        return value


class CodeNameParam(click.ParamType):
    """
    verify there is no @ sign in the name
    """
    name = 'code label'

    def convert(self, value, param, ctx):
        """
        check if valid code name
        """
        value = super(CodeNameParam, self).convert(value, param, ctx)
        if '@' in value:
            raise click.BadParameter("Code labels may not contain the '@' sign", param=param)
        return value
