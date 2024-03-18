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
from aiida.cmdline.params.types import CalculationParamType, WorkflowParamType
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.defaults import make_default_dump_path
from aiida.orm.nodes.process.calculation.calcjob import CalcJobNode
from aiida.orm.nodes.process.workflow.workchain import WorkChainNode
from aiida.tools.dumping.processes import ProcessNodeYamlDumper, calcjob_dump, workchain_dump

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
# @arguments.WORKFLOW(
#     'workchain',
#     type=(
#         WorkflowParamType(
#             sub_classes=('aiida.node:process.workflow.workchain', 'aiida.node:process.calculation.calcjob')
#         ),
#     ),
# )
@arguments.PROCESS()
@options.DUMP_PATH()
@options.NO_NODE_INPUTS()
@options.INCLUDE_ATTRIBUTES()
@options.INCLUDE_EXTRAS()
@options.USE_PREPARE_FOR_SUBMISSION()
@options.OVERWRITE()
def dump(
    process,
    path,
    no_node_inputs,
    include_attributes,
    include_extras,
    use_prepare_for_submission,
    overwrite
) -> None:
    """Dump files involved in the execution of a workflow.

    Child workflows and calculations called by the parent AiiDA `WorkChain` are contained in the tree as sub-folders and
    sorted by their creation time. The directory tree mirrors the hierarchy obtained when running `verdi process
    status`. For each calculation, input and output files can be found in the corresponding `raw_inputs` and
    `raw_outputs` directories. Additional input files (depending on the type of calculation) are placed in the
    `node_inputs` folder. Every folder also contains an `aiida_node_metadata.yaml` file with the relevant AiiDA node
    data.

    Note: This is for inspection only and not intended for direct resubmission of the simulations run by the
    workflow, as intermediate files can be missing.
    """

    # Instantiate YamlDumper
    processnode_dumper = ProcessNodeYamlDumper(include_attributes=include_attributes, include_extras=include_extras)

    # Make output directory
    output_path = make_default_dump_path(path=path, process_node=process, overwrite=overwrite)

    # Actual recursive function call
    if isinstance(process, WorkChainNode):
        workchain_dump(
            process_node=process,
            output_path=output_path,
            no_node_inputs=no_node_inputs,
            use_prepare_for_submission=use_prepare_for_submission,
            node_dumper=processnode_dumper,
        )
    elif isinstance(process, CalcJobNode):
        echo.echo_warning(
            f'''Command called on CalcJobNode. Will dump anyway, but `verdi calcjob dump <{process.uuid[:8]}>` should be
            used instead.'''
        )
        calcjob_dump(
            calcjob_node=process,
            output_path=output_path,
            no_node_inputs=no_node_inputs,
            use_prepare_for_submission=use_prepare_for_submission,
            node_dumper=processnode_dumper,
        )
    else:
        echo.echo_critical("<{workchain.uuid[:8]}> not a ProcessNode.")

    echo.echo_report(
        f'''Raw files for all calculations run by the `Workchain` <{process.uuid[:8]}> dumped successfully in directory
        "{output_path}".
        '''
    )
