# -*- coding: utf-8 -*-
"""
parameter type for AiiDA users
"""
import click
from click_completion import startswith
from click_spinner import spinner as cli_spinner

from aiida.cmdline.aiida_verdi.verdic_utils import aiida_dbenv


class UserParam(click.ParamType):
    """
    parameter type for arguments and options to pass and AiiDA user
    """
    name = 'aiida user'

    def __init__(self, convert=True, **kwargs):
        self.get_from_db = convert

    @aiida_dbenv
    def convert(self, value, param, ctx):
        """
        Returns a User instance if convert=True or the user's email else.
        """
        from aiida.orm.user import User
        '''guard against None values'''
        if not value:
            raise click.BadParameter('user parameter cannot be empty')

        '''get user with corresponding email (if value=None, returns all users)'''
        user_list = User.search_for_users(email=value)
        if not user_list:
            raise click.BadParameter('no user with email {} found'.format(value))

        '''return the email or convert to a User instance'''
        if self.get_from_db:
            value = user_list[0]
        return value

    @aiida_dbenv
    def complete(self, ctx=None, incomplete=''):
        """
        list users with email starting with incomplete
        """
        with cli_spinner():
            from aiida.orm.user import User
            return [(i.email, '{} {}'.format(i.first_name, i.last_name)) for i in User.search_for_users()]

    def get_missing_message(self, param):
        """
        returns the message to be printed on :py:class`click.MissingParameter`
        """
        users = ['{:<26} - {}'.format(*u) for u in self.complete()]
        return 'Possible arguments are:\n\n' + '\n'.join(users)
