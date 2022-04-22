# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Reusable command line interface options for Computer commands."""
import click

from aiida.cmdline.params import options, types
from aiida.cmdline.params.options.interactive import InteractiveOption, TemplateInteractiveOption
from aiida.cmdline.params.options.overridable import OverridableOption


def should_call_default_mpiprocs_per_machine(ctx):  # pylint: disable=invalid-name
    """
    Return True if the scheduler can accept 'default_mpiprocs_per_machine',
    False otherwise.

    If there is a problem in determining the scheduler, return True to
    avoid exceptions.
    """
    from aiida.common.exceptions import ValidationError

    scheduler_ep = ctx.params['scheduler']
    if scheduler_ep is not None:
        try:
            scheduler_cls = scheduler_ep.load()
        except ImportError:
            raise ImportError(f"Unable to load the '{scheduler_ep.name}' scheduler")
    else:
        raise ValidationError(
            'The should_call_... function should always be run (and prompted) AFTER asking for a scheduler'
        )

    job_resource_cls = scheduler_cls.job_resource_class
    if job_resource_cls is None:
        # Odd situation...
        return False

    return job_resource_cls.accepts_default_mpiprocs_per_machine()


LABEL = options.LABEL.clone(
    prompt='Computer label',
    cls=InteractiveOption,
    required=True,
    help='Unique, human-readable label for this computer.'
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

TRANSPORT = options.TRANSPORT.clone(prompt='Transport plugin', cls=InteractiveOption)

SCHEDULER = options.SCHEDULER.clone(prompt='Scheduler plugin', cls=InteractiveOption)

SHEBANG = OverridableOption(
    '--shebang',
    prompt='Shebang line (first line of each script, starting with #!)',
    default='#!/bin/bash',
    cls=InteractiveOption,
    help='Specify the first line of the submission script for this computer (only the bash shell is supported).',
    type=types.ShebangParamType()
)

WORKDIR = OverridableOption(
    '-w',
    '--work-dir',
    prompt='Work directory on the computer',
    default='/scratch/{username}/aiida/',
    cls=InteractiveOption,
    help='The absolute path of the directory on the computer where AiiDA will '
    'run the calculations (often a "scratch" directory).'
    'The {username} string will be replaced by your username on the remote computer.'
)

MPI_RUN_COMMAND = OverridableOption(
    '-m',
    '--mpirun-command',
    prompt='Mpirun command',
    default='mpirun -np {tot_num_mpiprocs}',
    cls=InteractiveOption,
    help='The mpirun command needed on the cluster to run parallel MPI programs. The {tot_num_mpiprocs} string will be '
    'replaced by the total number of cpus. See the scheduler docs for further scheduler-dependent template variables.',
    type=types.MpirunCommandParamType()
)

MPI_PROCS_PER_MACHINE = OverridableOption(
    '--mpiprocs-per-machine',
    prompt='Default number of CPUs per machine',
    cls=InteractiveOption,
    prompt_fn=should_call_default_mpiprocs_per_machine,
    required_fn=False,
    type=click.INT,
    help='The default number of MPI processes that should be executed per machine (node), if not otherwise specified.'
    'Use 0 to specify no default value.',
)

DEFAULT_MEMORY_PER_MACHINE = OverridableOption(
    '--default-memory-per-machine',
    prompt='Default amount of memory per machine (kB).',
    cls=InteractiveOption,
    type=click.INT,
    help='The default amount of RAM (kB) that should be allocated per machine (node), if not otherwise specified.'
)

USE_DOUBLE_QUOTES = OverridableOption(
    '--use-double-quotes/--not-use-double-quotes',
    default=False,
    cls=InteractiveOption,
    prompt='Escape CLI arguments in double quotes',
    help='Whether the command line arguments before and after the executable in the submission script should be '
    'escaped with single or double quotes.'
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
    footer='All lines that start with `#=` will be ignored.'
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
    footer='All lines that start with `#=` will be ignored.'
)
