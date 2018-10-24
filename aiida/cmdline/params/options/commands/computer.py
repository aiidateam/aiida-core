# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Reusable command line interface options for Computer commands."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from aiida.cmdline.params import options, types
from aiida.cmdline.params.options.interactive import InteractiveOption
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
            raise ImportError("Unable to load the '{}' scheduler".format(scheduler_ep.name))
    else:
        raise ValidationError(
            "The should_call_... function should always be run (and prompted) AFTER asking for a scheduler")

    job_resource_cls = scheduler_cls.job_resource_class
    if job_resource_cls is None:
        # Odd situation...
        return False

    return job_resource_cls.accepts_default_mpiprocs_per_machine()


LABEL = options.LABEL.clone(
    prompt='Computer label', cls=InteractiveOption, required=True, type=types.NonEmptyStringParamType())

HOSTNAME = options.HOSTNAME.clone(
    prompt='Hostname',
    cls=InteractiveOption,
    required=True,
    help='The fully qualified hostname of this computer; for local transports, use localhost.')

DESCRIPTION = options.DESCRIPTION.clone(
    prompt='Description', cls=InteractiveOption, help='A human-readable description of this computer.')

ENABLED = OverridableOption(
    '-e/-d',
    '--enabled/--disabled',
    is_flag=True,
    default=True,
    help='Calculations on disabled computers will not be submitted until the computer is re-enabled.',
    prompt='Enable the computer?',
    cls=InteractiveOption,
    # IMPORTANT! Do not specify explicitly type=click.BOOL,
    # Otherwise you would not get a default value when prompting
)

TRANSPORT = options.TRANSPORT.clone(prompt='Transport plugin', cls=InteractiveOption)

SCHEDULER = options.SCHEDULER.clone(prompt='Scheduler plugin', cls=InteractiveOption)

SHEBANG = OverridableOption(
    '--shebang',
    prompt='Shebang line (first line of each script, starting with #!)',
    default='#!/bin/bash',
    cls=InteractiveOption,
    help='This line specifies the first line of the submission script for this computer.',
    type=types.ShebangParamType())

WORKDIR = OverridableOption(
    '-w',
    '--work-dir',
    prompt='Work directory on the computer',
    default='/scratch/{username}/aiida/',
    cls=InteractiveOption,
    help='The absolute path of the directory on the computer where AiiDA will '
    'run the calculations (typically, the scratch of the computer). You '
    'can use the {username} replacement, that will be replaced by your '
    'username on the remote computer.')

MPI_RUN_COMMAND = OverridableOption(
    '-m',
    '--mpirun-command',
    prompt='Mpirun command',
    default='mpirun -np {tot_num_mpiprocs}',
    cls=InteractiveOption,
    help='The mpirun command needed on the cluster to run parallel MPI '
    'programs. You can use the {tot_num_mpiprocs} replacement, that will be '
    'replaced by the total number of cpus, or the other scheduler-dependent '
    'replacement fields (see the scheduler docs for more information).',
    type=types.MpirunCommandParamType())

MPI_PROCS_PER_MACHINE = OverridableOption(
    '--mpiprocs-per-machine',
    prompt='Default number of CPUs per machine',
    cls=InteractiveOption,
    prompt_fn=should_call_default_mpiprocs_per_machine,
    required_fn=False,
    type=click.INT,
    help='Enter here the default number of MPI processes per machine (node) that '
    'should be used if nothing is otherwise specified. Pass the digit 0 '
    'if you do not want to provide a default value.',
)
