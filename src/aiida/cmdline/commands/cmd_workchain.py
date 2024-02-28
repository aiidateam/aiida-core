###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi workchain` commands."""


import pathlib

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments
from aiida.cmdline.params.types import WorkflowParamType
from aiida.cmdline.utils import echo
from aiida.tools.dumping.processes import ProcessNodeYamlDumper, recursive_dump

# TODO I have several other cli functions that are useful for
# my own work, but somehow it's not easy to merge them
# here, e.g.,
#   My original version supports gotocomputer for
#   workchain, calcjob, RemoteData, or RemoteStashFolderData,
#   this is convenient for user, but since we are now in
#   the workchain namespace, we shouldn't add support for
#   RemoteData and RemoteStashFolderData here, but I hope
#   we can put it somewhere and ideally the cli command should
#   be easy to remember.
#   https://github.com/aiidateam/aiida-wannier90-workflows/blob/2e8c912fa1f5fcbbbbb0478e116c8f73c2ffd048/src/aiida_wannier90_workflows/cli/node.py#L274-L277

# TODO same as above, the other cli commands in the aiida-wannier90-workflows
# package support both calcjob and workchain at the same time, this is
# convenient for the user (less to remember), but here for the sake of
# conceptual cleanliness, the cli commands in aiida-core is split into
# calcjob and workchain. In addition, the implementation for calcjob and
# workchain cli commands are similar, we should try to merge them into one.


@verdi.group('workchain')
def verdi_workchain():
    """Inspect and manage workchains."""


@verdi_workchain.command('dump')
@arguments.WORKFLOW('workchain', type=WorkflowParamType(sub_classes=('aiida.node:process.workflow.workchain',)))
@click.option(
    '--path',
    '-p',
    type=click.Path(),
    default='.',
    show_default=True,
    help='The main directory to save the files involved in the workchain.',
)
@click.option(
    '--no-node-inputs',
    '-n',
    is_flag=True,
    default=False,
    show_default=True,
    help='Turn off dumping the input nodes of the `CalcJob`.',
)
@click.option(
    '--include-attributes',
    '-a',
    is_flag=True,
    default=False,
    show_default=True,
    help='Include attributes in the `aiida_node_metadata.yaml` which is written for each ProcessNode.',
)
@click.option(
    '--include-extras',
    '-e',
    is_flag=True,
    default=False,
    show_default=True,
    help='Include extras in the `aiida_node_metadata.yaml` which is written for each ProcessNode.',
)
@click.option(
    '--use-prepare-for-submission',
    '-u',
    is_flag=True,
    default=False,
    show_default=True,
    help='Use the `prepare_for_submission` method of the respective `CalcJobs`. Note: this requireds the corresponding aiida-plugin to be installed.',
)
def workchain_dump(
    workchain,
    path,
    no_node_inputs,
    include_attributes,
    include_extras,
    use_prepare_for_submission,
) -> None:
    """Dump files involved in the execution of the workchain.

    Note: This is for inspection only and does not guarantee tha a direct resubmission of the simulations is possible.
    """

    # Set reasonable default path when path argument is omitted
    if path == '.':
        path = f'dump-{workchain.pk}'
    output_path = pathlib.Path(path)

    # Check if path already exists
    try:
        pathlib.Path(output_path).mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        echo.echo_critical(f'Invalid value for "OUTPUT_PATH": Path "{output_path}" exists.')

    # Write parent node_metadata
    processnode_dumper = ProcessNodeYamlDumper(include_attributes=include_attributes, include_extras=include_extras)
    processnode_dumper.dump_yaml(process_node=workchain, output_path=output_path)

    # Actual recursive function call
    recursive_dump(
        process_node=workchain,
        output_path=output_path,
        no_node_inputs=no_node_inputs,
        use_prepare_for_submission=use_prepare_for_submission,
        node_dumper=processnode_dumper,
    )
