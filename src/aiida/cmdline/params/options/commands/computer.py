###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Reusable command line interface options for Computer commands."""

import typing as t

import click

from aiida.cmdline.params import options, types
from aiida.cmdline.params.options.interactive import InteractiveOption, TemplateInteractiveOption
from aiida.cmdline.params.options.overridable import OverridableOption
from aiida.cmdline.utils import echo

if t.TYPE_CHECKING:
    from aiida.schedulers.datastructures import JobResource


def get_job_resource_cls(ctx: click.Context) -> 'type[JobResource]':
    """Return job resource cls from ctx."""
    from aiida.common.exceptions import ValidationError
    from aiida.schedulers import Scheduler

    scheduler_ep = ctx.params['scheduler']
    if scheduler_ep is not None:
        try:
            scheduler_cls = t.cast(Scheduler, scheduler_ep.load())
        except ImportError:
            raise ImportError(f"Unable to load the '{scheduler_ep.name}' scheduler")
    else:
        raise ValidationError(
            'The should_call_... function should always be run (and prompted) AFTER asking for a scheduler'
        )

    return scheduler_cls.job_resource_class


def should_call_default_mpiprocs_per_machine(ctx: click.Context) -> bool:
    """Return whether the selected scheduler type accepts `default_mpiprocs_per_machine`.

    :return: `True` if the scheduler type accepts `default_mpiprocs_per_machine`, `False`
        otherwise. If the scheduler class could not be loaded `False` is returned by default.
    """
    job_resource_cls = get_job_resource_cls(ctx)
    if job_resource_cls is None:
        # Odd situation...
        return False  # type: ignore[unreachable]

    return job_resource_cls.accepts_default_mpiprocs_per_machine()


def should_call_default_memory_per_machine(ctx: click.Context) -> bool:
    """Return whether the selected scheduler type accepts `default_memory_per_machine`.

    :return: `True` if the scheduler type accepts `default_memory_per_machine`, `False`
        otherwise. If the scheduler class could not be loaded `False` is returned by default.
    """
    job_resource_cls = get_job_resource_cls(ctx)

    if job_resource_cls is None:
        # Odd situation...
        return False  # type: ignore[unreachable]

    return job_resource_cls.accepts_default_memory_per_machine()


LABEL = options.LABEL.clone(
    prompt='Computer label',
    cls=InteractiveOption,
    required=True,
    help='Unique, human-readable label for this computer.',
)

HOSTNAME = options.HOSTNAME.clone(
    prompt='Hostname',
    cls=InteractiveOption,
    required=True,
    help='The fully qualified hostname of the computer (e.g. daint.cscs.ch). '
    'Use "localhost" when setting up the computer that AiiDA is running on.',
)

DESCRIPTION = options.DESCRIPTION.clone(
    prompt='Description', cls=InteractiveOption, help='A human-readable description of this computer.'
)


def transport_callback(ctx: click.Context, param: click.Parameter, value: t.Any) -> t.Any:
    """Callback for the transport option that shows a deprecation warning for core.ssh."""
    if value is not None and value.name == 'core.ssh':
        echo.echo_deprecated(
            'The `core.ssh` transport plugin is deprecated and will be removed in v3.0. '
            'Use `core.ssh_async` instead, which is significantly faster and provides an '
            'easier configuration interface.'
        )
    return value


TRANSPORT = options.TRANSPORT.clone(prompt='Transport plugin', cls=InteractiveOption, callback=transport_callback)

SCHEDULER = options.SCHEDULER.clone(prompt='Scheduler plugin', cls=InteractiveOption)

SHEBANG = OverridableOption(
    '--shebang',
    prompt='Shebang line (first line of each script, starting with #!)',
    default='#!/bin/bash',
    cls=InteractiveOption,
    help='Specify the first line of the submission script for this computer (only the bash shell is supported).',
    type=types.ShebangParamType(),
)

WORKDIR = OverridableOption(
    '-w',
    '--work-dir',
    prompt='Work directory on the computer',
    default='/scratch/{username}/aiida/',
    cls=InteractiveOption,
    help='The absolute path of the directory on the computer where AiiDA will '
    'run the calculations (often a "scratch" directory).'
    'The {username} string will be replaced by your username on the remote computer.',
)

MPI_RUN_COMMAND = OverridableOption(
    '-m',
    '--mpirun-command',
    prompt='Mpirun command',
    default='mpirun -np {tot_num_mpiprocs}',
    cls=InteractiveOption,
    help='The mpirun command needed on the cluster to run parallel MPI programs. The {tot_num_mpiprocs} string will be '
    'replaced by the total number of cpus. See the scheduler docs for further scheduler-dependent template variables.',
    type=types.MpirunCommandParamType(),
)

MPI_PROCS_PER_MACHINE = OverridableOption(
    '--mpiprocs-per-machine',
    prompt='Default number of CPUs per machine',
    cls=InteractiveOption,
    prompt_fn=should_call_default_mpiprocs_per_machine,
    required=False,
    type=click.INT,
    help='The default number of MPI processes that should be executed per machine (node), if not otherwise specified.',
)

DEFAULT_MEMORY_PER_MACHINE = OverridableOption(
    '--default-memory-per-machine',
    prompt='Default amount of memory per machine (kB).',
    cls=InteractiveOption,
    prompt_fn=should_call_default_memory_per_machine,
    required=False,
    type=click.INT,
    help='The default amount of RAM (kB) that should be allocated per machine (node), if not otherwise specified.',
)

USE_DOUBLE_QUOTES = OverridableOption(
    '--use-double-quotes/--not-use-double-quotes',
    default=False,
    cls=InteractiveOption,
    prompt='Escape CLI arguments in double quotes',
    help='Whether the command line arguments before and after the executable in the submission script should be '
    'escaped with single or double quotes.',
)

PREPEND_TEXT = OverridableOption(
    '--prepend-text',
    cls=TemplateInteractiveOption,
    prompt='Prepend script',
    type=click.STRING,
    default='',
    help='Bash commands that should be prepended to the executable call in all submit scripts for this computer.',
    extension='.bash',
    header='PREPEND_TEXT: if there is any bash commands that should be prepended to the executable call in all '
    'submit scripts for this computer, type that between the equal signs below and save the file.',
    footer='All lines that start with `#=` will be ignored.',
)

APPEND_TEXT = OverridableOption(
    '--append-text',
    cls=TemplateInteractiveOption,
    prompt='Append script',
    type=click.STRING,
    default='',
    help='Bash commands that should be appended to the executable call in all submit scripts for this computer.',
    extension='.bash',
    header='APPEND_TEXT: if there is any bash commands that should be appended to the executable call in all '
    'submit scripts for this computer, type that between the equal signs below and save the file.',
    footer='All lines that start with `#=` will be ignored.',
)
