###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi workchain` commands."""

import click

from aiida import orm
from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments
from aiida.cmdline.params.types import WorkflowParamType
from aiida.cmdline.utils import echo
from aiida.common import LinkType

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


def _get_input_filename(calcjob: orm.CalcJobNode) -> str:
    """Get the input filename of a CalcJob."""

    # TODO copied from
    # https://github.com/aiidateam/aiida-core/blob/06ea130df8854f621e25853af6ac723c37397ed0/src/aiida/cmdline/commands/cmd_calcjob.py#L90-L106
    # should be deduplicated

    # Get path from the given CalcJobNode if not defined by user
    path = calcjob.get_option('input_filename')

    # Get path from current process class of CalcJobNode if still not defined
    if path is None:
        fname = calcjob.process_class.spec_options.get('input_filename')
        if fname and fname.has_default():
            path = fname.default

    if path is None:
        # Still no path available
        echo.echo_critical(
            '"{}" and its process class "{}" do not define a default input file '
            '(option "input_filename" not found).\n'
            'Please specify a path explicitly.'.format(calcjob.__class__.__name__, calcjob.process_class.__name__)
        )
    return path


@verdi_workchain.command('inputsave')
@arguments.WORKFLOW('workchain', type=WorkflowParamType(sub_classes=('aiida.node:process.workflow.workchain',)))
@click.option(
    '--path',
    '-p',
    type=click.Path(),
    default='.',
    show_default=True,
    help='The directory to save all the input files.',
)
@click.pass_context
def workchain_inputsave(ctx, workchain, path):
    """Save input files of a workchain."""
    from contextlib import redirect_stdout
    from pathlib import Path

    from aiida.cmdline.commands.cmd_calcjob import calcjob_inputcat

    dir_path = Path(path)
    if not dir_path.exists():
        dir_path.mkdir()

    links = workchain.base.links.get_outgoing(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).all()
    links.sort(key=lambda x: x.node.ctime)

    for i, link in enumerate(links):
        link_label = link.link_label
        called = link.node
        subdir_path = dir_path / f'{i+1}-{link_label}'
        subdir_path.mkdir()

        if isinstance(called, orm.WorkChainNode):
            ctx.invoke(workchain_inputsave, workchain=called, path=subdir_path)
        else:
            save_path = subdir_path / _get_input_filename(called)
            with open(save_path, 'w', encoding='utf-8') as handle:
                with redirect_stdout(handle):
                    ctx.invoke(calcjob_inputcat, calcjob=called)
                echo.echo(f'Saved to {save_path}')
