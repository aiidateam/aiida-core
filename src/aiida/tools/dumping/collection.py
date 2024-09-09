# Could also be a more general CollectionDumper class, actually
# TODO: Have a `full_raw` flag or sthg that dumps all the raw calculations to disk anyway

import contextlib
from aiida.common import timezone
from aiida.orm import CalculationNode, Code, Computer, Group, QueryBuilder, StructureData, User, WorkflowNode
from aiida import orm
from typing import List
from aiida.tools.dumping.utils import _validate_make_dump_path, get_nodes_from_db
from pathlib import Path
from aiida.tools.dumping.process import ProcessDumper
import itertools

# DEFAULT_ENTITIES_TO_DUMP = [WorkflowNode, StructureData, User, Code, Computer]
DEFAULT_ENTITIES_TO_DUMP = [CalculationNode, WorkflowNode]  # , StructureData, User, Code, Computer]

# from aiida.common.utils import str_timedelta


class GroupDumper:
    def __init__(
        self,
        group: orm.Group | str | None = None,
        entities_to_dump: List | None = None,
        output_path: Path | str | None = None,
    ) -> None:

        if entities_to_dump is None:
            self.entities_to_dump = DEFAULT_ENTITIES_TO_DUMP

        from aiida.manage import get_manager

        self.profile = get_manager().get_profile()

        if output_path is None:
            output_path = Path.cwd()
        self.output_path = output_path

        self.group = group

    def dump(self, group):
        self.last_dumped = timezone.now()

        try:
            group_name = group.label
        except AttributeError:
            group_name = group

        if self.group is None:
            self.group = group

        # self.parent_path =
        # Path(f'group-dump_{self.profile.name}_{group_name}_{self.last_dumped.strftime("%Y-%m-%d")}')

        self.hidden_aiida_path = self.output_path / '.aiida-raw-data'
        # self.group_path = Path.cwd() / 'groups'
        self.group_path = self.output_path / 'groups' / group_name

        print('SELF.HIDDEN_AIIDA_PATH', self.hidden_aiida_path)

        # First dump empty in default, hidden AiiDA dumping directory
        # Then create the symlinking

        print('GROUP', group, self.group, group.label, str(self.group))

        # print('_DUMP_TO_HIDDEN(SELF, AIIDA_ENTITY, AIIDA_NODES)')
        # print(entity, len(group_nodes))

        # print("ABC", aiida_entity==CalculationNode)
        # if :

        self._dump_calculations_hidden()
        self._dump_link_workflows()

        # for entity in self.entities_to_dump:

        #     group_nodes = get_nodes_from_db(aiida_node_type=entity, with_group=group, flatten=True)

        #     # print('_DUMP_TO_HIDDEN(SELF, AIIDA_ENTITY, AIIDA_NODES)')
        #     # print(entity, len(group_nodes))

        #     # print("ABC", aiida_entity==CalculationNode)
        #     if entity==CalculationNode:
        #         print('SELF._DUMP_CALCULATIONS_HIDDEN', len(group_nodes))
        #         self._dump_calculations_hidden(calculations=group_nodes)

        #     # if entity==WorkflowNode:
        #     #     print('SELF._DUMP_WORKFLOWS_HIDDEN', len(group_nodes))
        #     #     self._dump_workflows_hidden(workflows=group_nodes)

    def _dump_calculations_hidden(self):
        # ? Dump only top-level workchains, as that includes sub-workchains already

        # Obtain all `CalculationNode`s that are directly assigned to the group
        print('group in hidden', self.group)
        if self.group is None:
            raise Exception('`group` must be set.')

        direct_calc_nodes = get_nodes_from_db(aiida_node_type=CalculationNode, with_group=self.group, flatten=True)

        # Obtain all `CalculationNode`s that were called within
        workflow_nodes = get_nodes_from_db(aiida_node_type=orm.WorkflowNode, with_group=self.group, flatten=True)
        workflow_sub_nodes = itertools.chain(*[workflow_node.called_descendants for workflow_node in workflow_nodes])
        indirect_calc_nodes = [
            workflow_sub_node
            for workflow_sub_node in workflow_sub_nodes
            if isinstance(workflow_sub_node, CalculationNode)
        ]

        calculations = set(direct_calc_nodes + indirect_calc_nodes)

        print('SELF._DUMP_CALCULATIONS_HIDDEN', len(calculations))

        for calculation in calculations:
            # ? Hardcode overwrite=True for now
            calculation_dumper = ProcessDumper(overwrite=True)

            calculation_dump_path = self.hidden_aiida_path / 'calculations' / calculation.uuid
            print(calculation_dump_path)

            # if not self.dry_run:
            # with contextlib.suppress(FileExistsError):
            try:
                # TODO: Use private `_dump_calculation` instead
                calculation_dumper.dump(process_node=calculation, output_path=calculation_dump_path)
            except:
                raise


            # # To make development quicker
            # if iworkflow_ > 1:
            #     break

    def _dump_link_workflows(self):



        workflow_nodes = get_nodes_from_db(aiida_node_type=orm.WorkflowNode, with_group=self.group, flatten=True)
        for workflow_node in workflow_nodes:
            workflow_dumper = ProcessDumper(overwrite=True)

            calculation_link_path = self.hidden_aiida_path / 'calculations'
            # TODO: If the GroupDumper is called from somewhere else outside, prefix the path with `groups/core` etc
            workflow_dump_path = self.output_path / Path(self.group.label) / 'workflows'

            workflow_dumper._dump_workflow(
                workflow_node=workflow_node,
                output_path=workflow_dump_path,
                link_calculation=True,
                calculation_dir=calculation_link_path

            )


    # def _dump_workflows_hidden(self, workflows, only_parents: bool = True):
    #     # ? Dump only top-level workchains, as that includes sub-workchains already
    #     # ? Apart from the yaml files, all the files are contained in the calculations anyways??

    #     for iworkflow_, workflow in enumerate(workflows):
    #         # if only_parents and workflow.caller is not None:
    #         #     continue

    #         # ? Hardcode overwrite=True for now
    #         workflow_dumper = ProcessDumper(overwrite=True)

    #         workflow_dump_path = self.hidden_aiida_path / 'workflows' / workflow.uuid
    #         print(workflow_dump_path)

    #         # if not self.dry_run:
    #         with contextlib.suppress(FileExistsError):
    #             workflow_dumper.dump(process_node=workflow, output_path=workflow_dump_path)

    #         # self.entity_counter_dictionary[WorkflowNode.__name__] += 1

    #         # # To make development quicker
    #         # if iworkflow_ > 1:
    #         #     break
