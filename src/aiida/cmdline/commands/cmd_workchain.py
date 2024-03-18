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
from aiida.orm.nodes.process.workflow.workchain import WorkChainNode
from aiida.tools.dumping.processes import process_dump


@verdi.group('workchain')
def verdi_workchain():
    """Inspect and manage workchains."""

@verdi_workchain.command('dump')
@arguments.PROCESS()
@options.DUMP_PATH()
@options.NO_NODE_INPUTS()
@options.INCLUDE_ATTRIBUTES()
@options.INCLUDE_EXTRAS()
@options.USE_PREPARE_FOR_SUBMISSION()
@options.OVERWRITE()
def workchain_dump_wrapper(**kwargs) -> None:
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

    process_dump(process_type=WorkChainNode, **kwargs)
