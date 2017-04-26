#-*- coding: utf8 -*-
"""
utilities for accessing aiida entities from commandline commands
"""


from aiida.cmdline.aiida_verdi.verdic_utils import aiida_dbenv
from aiida.cmdline.aiida_verdi.verdic_utils import load_dbenv_if_not_loaded as ensure_aiida_dbenv


@aiida_dbenv
def get_computer(name):
    """
    Get a Computer object with given name, or raise NotExistent
    """
    from aiida.orm.computer import Computer as AiidaOrmComputer

    return AiidaOrmComputer.get(name)


@aiida_dbenv
def get_computer_names():
    """
    Retrieve the list of computers in the DB.

    ToDo: use an API or cache the results, sometime it is quite slow!
    """
    from aiida.orm.querybuilder import QueryBuilder
    qb = QueryBuilder()
    qb.append(type='computer', project=['name'])
    if qb.count() > 0:
        return zip(*qb.all())[0]
    else:
        return None


@aiida_dbenv
def create_computer(**kwargs):
    """
    Create a computer instance in a storable state from kwargs

    :kwarg label: name of the computer
    :kwarg description: description
    :kwarg hostname: fully qualified hostname
    :kwarg bool enabled_state: True for enabled, False for disabled
    :kwarg transport: name of a valid transport plugin
    :kwarg scheduler: name of a valid scheduler plugin
    :kwarg workdir: directory in which to run jobs ({username} wildcard can be used)
    :kwarg mpirun: mpirun command string
    :kwarg ppm: (int) processors per machine
    :kwarg prepend_text: bash code to run before every command execution
    :kwarg append_text: bash code to run after every command execution
    """
    from aiida.orm import Computer

    computer = Computer(name=kwargs['label'])
    computer._set_description_string(kwargs['description'])
    computer._set_hostname_string(kwargs['hostname'])
    computer.set_enabled_state(kwargs['enabled'])
    computer._set_transport_type_string(kwargs['transport'])
    computer._set_scheduler_type_string(kwargs['scheduler'])
    computer._set_workdir_string(kwargs['workdir'])
    computer._set_mpirun_command_string(kwargs['mpirun'])
    computer.set_default_mpiprocs_per_machine(kwargs['ppm'])
    computer._set_prepend_text_string(kwargs['prepend_text'])
    computer._set_append_text_string(kwargs['append_text'])

    return computer


def comp_not_exists(ctx, param, value):
    import click
    from aiida.common.exceptions import NotExistent
    from aiida.cmdline.aiida_verdi.utils.aiidadb import get_computer
    if not value:
        return value
        # ~ raise click.MissingParameter(param=param)
    try:
        get_computer(name=value)
        msg = '{} exists. '.format(value)
        msg += 'Use verdi computer update to modify existing computers'
        raise click.ClickException(msg)
    except NotExistent:
        return value
    except TypeError:
        raise click.BadParameter('must be a valid string', param=param)

