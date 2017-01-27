#-*- coding: utf8 -*-
"""
main group and entry point for the verdi commandline
"""
import click
from click_plugins import with_plugins
from click_completion import init as cpl_init
from pkg_resources import iter_entry_points

cpl_init()


@with_plugins(iter_entry_points('aiida.cmdline'))
@click.group()
@click.option('-p', '--profile', metavar='PROFILENAME')
def verdi_plug(profile):
    """
    The commandline interface to AiiDA
    """
    from aiida.backends import settings as settings_profile
    # We now set the internal variable, if needed
    if profile is not None:
        settings_profile.AIIDADB_PROFILE = profile
    # I set the process to verdi
    settings_profile.CURRENT_AIIDADB_PROCESS = "verdi"
