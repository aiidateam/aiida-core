# -*- coding: utf8 -*-
"""
standard options for consistency throughout the verdi commandline
"""
import click

from aiida.backends.profile import (BACKEND_DJANGO, BACKEND_SQLA)
from aiida.cmdline.aiida_verdi.param_types.plugin import PluginParam
from aiida.cmdline.aiida_verdi.param_types.computer import ComputerParam
from aiida.cmdline.aiida_verdi.param_types.user import UserParam
from aiida.cmdline.aiida_verdi.param_types.jobcalc import JobCalcParam
from aiida.cmdline.aiida_verdi.verdic_utils import prompt_with_help, multi_line_prompt


class overridable_option(object):
    """
    wrapper around click option that allows to store the name
    and some defaults but also to override them later, for example
    to change the help message for a certain command.
    """
    def __init__(self, *args, **kwargs):
        """
        store the defaults.
        """
        self.args = args
        self.kwargs = kwargs

    def __call__(self, **kwargs):
        """
        override kwargs (no name changes) and return option
        """
        kw_copy = self.kwargs.copy()
        kw_copy.update(kwargs)
        return click.option(*self.args, **kw_copy)


label = overridable_option('-L', '--label', help='short text to be used as a label')

user = overridable_option('-u', '--user', type=UserParam())

description = overridable_option('-D', '--description', help='(text) description')

input_plugin = overridable_option('--input-plugin', help='input plugin string',
                                  type=PluginParam(category='calculations'))

force = overridable_option('-f', '--force', is_flag=True, help='Do not ask for confirmation')

past_days = overridable_option('-p', '--past-days', metavar='N', type=int, help="filter for only the past N days")

calculation = overridable_option('-c', '--calc', type=JobCalcParam(), help='PK or UUID of a calculation')

path = overridable_option('-p', '--path', type=click.Path(readable=False))

color = overridable_option('-c', '--color', is_flag=True)

computer = overridable_option('-C', '--computer', type=ComputerParam(),
                              help=('The name of the computer as stored in '
                                    'the AiiDA database'))

backend = overridable_option('--backend', type=click.Choice([BACKEND_DJANGO, BACKEND_SQLA],),
                             help='backend choice')

email = overridable_option('--email', metavar='EMAIL', type=str,
                           help='valid email address for the user')

db_host = overridable_option('--db-host', metavar='HOSTNAME', type=str,
                             help='database hostname')

db_port = overridable_option('--db-port', metavar='PORT', type=int,
                             help='database port')

db_name = overridable_option('--db-name', metavar='DBNAME', type=str,
                             help='database name')

db_user = overridable_option('--db-user', metavar='DBUSER', type=str,
                             help='database username')

db_pass = overridable_option('--db-pass', metavar='DBPASS', type=str,
                             help='password for username to access the database')

first_name = overridable_option('--first-name', metavar='FIRST', type=str,
                                help='your first name')

last_name = overridable_option('--last-name', metavar='LAST', type=str,
                               help='your last name')

institution = overridable_option('--institution', metavar='INSTITUTION', type=str,
                                 help='your institution')

repo = overridable_option('--repo', metavar='PATH', type=click.Path(),
                          help='data file repository')

remote_abs_path = overridable_option('--remote-abs-path', type=click.Path(file_okay=True),
                                     help=('[if --installed]: The (full) absolute path on the remote ' 'machine'))

non_interactive = overridable_option('--non-interactive', is_flag=True, is_eager=True,
                                     help='noninteractive mode: never prompt the user for input')

dry_run = overridable_option('--dry-run', is_flag=True, is_eager=True,
                             help='do not commit to database or modify configuration files')

debug = overridable_option('--debug', is_flag=True, is_eager=True,
                           help='print debug information')

prepend_callback = prompt_with_help(
    prompt=('Text to prepend to each command execution\n'
            'FOR INSTANCE MODULES TO BE LOADED FOR THIS CODE'),
    prompt_loop=multi_line_prompt
)

# ~ prepend_text = overridable_option('--prepend-text', callback=prepend_callback, help='Text to prepend to each command execution. FOR INSTANCE, MODULES TO BE LOADED FOR THIS CODE. This is a multiline string, whose content will be prepended inside the submission script after the real execution of the job. It is your responsibility to write proper bash code!')
prepend_text = overridable_option('--prepend-text', type=str, default='',
                                  help='Text to prepend to each command execution. FOR INSTANCE, MODULES TO BE LOADED FOR THIS CODE. This is a multiline string, whose content will be prepended inside the submission script after the real execution of the job. It is your responsibility to write proper bash code!')

append_callback = prompt_with_help(
    prompt='Text to append to each command execution',
    prompt_loop=multi_line_prompt
)

# ~ append_text = overridable_option('--append-text', callback=append_callback, help='Text to append to each command execution. This is a multiline string, whose content will be appended inside the submission script after the real execution of the job. It is your responsibility to write proper bash code!')
append_text = overridable_option('--append-text', type=str, default='',
                                 help='Text to append to each command execution. This is a multiline string, whose content will be appended inside the submission script after the real execution of the job. It is your responsibility to write proper bash code!')
