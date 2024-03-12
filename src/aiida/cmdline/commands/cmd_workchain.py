###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi workchain` commands."""

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.params.types import WorkflowParamType
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.defaults import make_default_dump_path
from aiida.tools.dumping.processes import ProcessNodeYamlDumper, workchain_dump

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
@options.DUMP_PATH()
@options.NO_NODE_INPUTS()
@options.INCLUDE_ATTRIBUTES()
@options.INCLUDE_EXTRAS()
@options.USE_PREPARE_FOR_SUBMISSION()
@options.OVERWRITE()
def dump(
    workchain,
    path,
    no_node_inputs,
    include_attributes,
    include_extras,
    use_prepare_for_submission,
    overwrite
) -> None:
    """Dump files involved in the execution of a `WorkChain`.

    Note: This is for inspection only and not intended for direct resubmission of the simulations run by the
    `WorkChain`, as intermediate files are likely missing.
    """

    # Instantiate YamlDumper
    processnode_dumper = ProcessNodeYamlDumper(include_attributes=include_attributes, include_extras=include_extras)

    # Make output directory
    output_path = make_default_dump_path(path=path, process_node=workchain, overwrite=overwrite)

    # Actual recursive function call
    workchain_dump(
        process_node=workchain,
        output_path=output_path,
        no_node_inputs=no_node_inputs,
        use_prepare_for_submission=use_prepare_for_submission,
        node_dumper=processnode_dumper,
    )

    echo.echo_report(
        f'''Workchain <{workchain.uuid[:8]}> dumped successfully in directory <{output_path}>.

        The root directory is `dump-<uuid>` or the name specified via `-p/--path`. The tree mirrors the hierachy
        obtained when running `verdi process status {workchain.uuid[:8]}`.

        Called `WorkChain`s and `Calcjob`s are contained in the tree as sub-folders and sorted by their creation time.
        For each `CalcJob`, input and output files can be found in the corresponding `raw_inputs` and `raw_outputs`
        directories. Additional input files (depending on the type of calculation) are placed in the `node_inputs`
        folder. Every folder also contains an `aiida_node_metadata.yaml` file with the relevant AiiDA node data.
        '''
    )
