
import contextlib
import itertools
import logging
import os
from pathlib import Path
from typing import List

from aiida import orm
from aiida.common import timezone

from aiida.tools.dumping.collection import CollectionDumper
from aiida.tools.dumping.process import ProcessDumper
from aiida.tools.dumping.data import DataDumper

from aiida.tools.dumping.utils import _validate_make_dump_path, get_nodes_from_db

# DEFAULT_ENTITIES_TO_DUMP = [WorkflowNode, StructureData, User, Code, Computer]
DEFAULT_PROCESSES_TO_DUMP = [orm.CalculationNode, orm.WorkflowNode]  # , StructureData, User, Code, Computer]
DEFAULT_DATA_TO_DUMP = [orm.StructureData, orm.Code, orm.Computer, ]  # , StructureData, User, Code, Computer]
DEFAULT_ENTITIES_TO_DUMP = DEFAULT_PROCESSES_TO_DUMP + DEFAULT_DATA_TO_DUMP

# from aiida.common.utils import str_timedelta

logger = logging.getLogger(__name__)


class GroupDumper(CollectionDumper):
    
    def __init__(self, entities_to_dump: List | None = None, **kwargs) -> None:
        super().__init__(**kwargs)

        if entities_to_dump is None:
            self.entities_to_dump = DEFAULT_ENTITIES_TO_DUMP

    # ? For now, only set dumping
    def dump(self, group: orm.Group | str | None = None, output_path: Path | str | None = None):
        # ? Here, these could be all kinds of entities that could be grouped in AiiDA
        # if output_path is None:
        #     output_path = Path.cwd()

        self.last_dumped = timezone.now()
        self.group = group

        if output_path is None:
            try:
                output_path = self.parent_path / 'groups'
            except:
                raise ValueError("Error setting up `output_path`. Must be set manually.")
        else:
            # TODO: Add validation here
            output_path.mkdir(exist_ok=True, parents=True)

        if isinstance(group, orm.Group):
            group_name = group.label
        elif isinstance(group, str):
            group_name = group
        else:
            raise Exception('Group must be set')

        self.entity_counter = self.create_entity_counter(orm_collection=self.group)
        # logger.report(f'SELF.ENTITY_COUNTER <{self.entity_counter}>')
        # self.entity_counter = self.create_entity_counter(orm_collection=self.group)

        # LOGGER.report(self.create_entity_counter(orm_collection=self.group))
        # raise SystemExit()

        # self.parent_path =
        # Path(f'group-dump_{self.profile.name}_{group_name}_{self.last_dumped.strftime("%Y-%m-%d")}')

        self.hidden_aiida_path = self.parent_path / '.aiida-raw-data'

        # ? This here now really relates to each individual group
        self.output_path = output_path
        # self.group_path = Path.cwd() / 'groups'
        # self.group_path = self.output_path / 'groups' / group_name

      # logger.report(f'self.entity_counter for Group <{self.group}>: {self.entity_counter}')
      # logger.report(f'Dumping calculations and workflows of group {group_name}...')

        # TODO: This shouldn't be on a per-group basis? Possibly dump all data for the whole profile.
        # TODO: Though, now that I think about it, it might actually be desirable to only limit that to the group only.
      # logger.report(f'Dumping raw calculation data for group {group_name}...')

        logger.report(f'Dumping processes for group {group_name}...')
        self._dump_processes()


    def _dump_processes(self):

        if (
            sum(
                self.entity_counter.get(orm_process_class, 0)
                for orm_process_class in [
                    orm.CalcJobNode,
                    orm.CalcFunctionNode,
                ]
            )
            > 0
        ):
            self._dump_calculations_hidden()
            self._link_calculations_hidden()

        # logger.report(f'Linking workflows to calculations for group {group_name}...')
        if (
            sum(
                self.entity_counter.get(orm_process_class, 0)
                for orm_process_class in [
                    orm.WorkChainNode,
                    orm.WorkFunctionNode,
                    # orm.CalcJobNode,
                    # orm.CalcFunctionNode,
                ]
            )
            > 0
        ):
            self._dump_link_workflows()

        # Special case in which no `WorkflowNode`s are contained in the group
        if (
            sum(
                self.entity_counter.get(orm_process_class, 0)
                for orm_process_class in [
                    orm.WorkChainNode,
                    orm.WorkFunctionNode,
                ]
            )
            == 0
            and sum(
                self.entity_counter.get(orm_process_class, 0)
                for orm_process_class in [
                    orm.CalcJobNode,
                    orm.CalcFunctionNode,
                ]
            )
            > 0
        ):
            # logger.report('GROUP 3 DUMP CALCULATIONS')
            # if self.entity_counter.get(orm.WorkChainNode, 0):
            self._dump_calculations_hidden()
            self._link_calculations_hidden()

      # logger.report(f'Dumping other data nodes of group {group_name}...')

        # TODO: Here might also be pseudo.family.sssp, not just workflows/calculations

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
        if self.group is None:
            raise Exception('`group` must be set.')

        direct_calc_nodes = get_nodes_from_db(aiida_node_type=orm.CalculationNode, with_group=self.group, flat=True)

        # Obtain all `CalculationNode`s that were called within
        workflow_nodes = get_nodes_from_db(aiida_node_type=orm.WorkflowNode, with_group=self.group, flat=True)
        workflow_sub_nodes = itertools.chain(*[workflow_node.called_descendants for workflow_node in workflow_nodes])
        indirect_calc_nodes = [
            workflow_sub_node
            for workflow_sub_node in workflow_sub_nodes
            if isinstance(workflow_sub_node, orm.CalculationNode)
        ]

        calculations = set(direct_calc_nodes + indirect_calc_nodes)

        # print('SELF._DUMP_CALCULATIONS_HIDDEN', len(calculations))

        for calculation in calculations:
            # ? Hardcode overwrite=True for now
            calculation_dumper = ProcessDumper(overwrite=True)

            calculation_dump_path = self.hidden_aiida_path / 'calculations' / calculation.uuid

            # if not self.dry_run:
            # with contextlib.suppress(FileExistsError):
            try:
                calculation_dumper._dump_calculation(calculation_node=calculation, output_path=calculation_dump_path)
            except:
                raise

            # # To make development quicker
            # if iworkflow_ > 1:
            #     break

    def _dump_link_workflows(self, link_calculations: bool = True):
        workflow_nodes = get_nodes_from_db(aiida_node_type=orm.WorkflowNode, with_group=self.group, flat=True)
        for workflow_node in workflow_nodes:
            workflow_dumper = ProcessDumper(overwrite=True)

            link_calculations_dir = self.hidden_aiida_path / 'calculations'
            # TODO: If the GroupDumper is called from somewhere else outside, prefix the path with `groups/core` etc
            workflow_dump_path = (
                self.output_path / 'workflows' / workflow_dumper._generate_default_dump_path(process_node=workflow_node)
            )
          # logger.report(f'WORKFLOW_DUMP_PATH: {workflow_dump_path}')

            workflow_dumper._dump_workflow(
                workflow_node=workflow_node,
                output_path=workflow_dump_path,
                link_calculations=link_calculations,
                link_calculations_dir=link_calculations_dir,
            )

    def _link_calculations_hidden(self):
        calculation_nodes = get_nodes_from_db(aiida_node_type=orm.CalculationNode, with_group=self.group, flat=True)
        for calculation_node in calculation_nodes:
            calculation_dumper = ProcessDumper(overwrite=True)

            link_calculations_dir = self.hidden_aiida_path / 'calculations'
            # link_calculations_dir.mkdir(parents=True, exist_ok=True)

            # TODO: If the GroupDumper is called from somewhere else outside, prefix the path with `groups/core` etc
            calculation_dump_path = self.output_path / 'calculations'
            calculation_dump_path.mkdir(parents=True, exist_ok=True)
            calculation_dump_path = calculation_dump_path / calculation_dumper._generate_default_dump_path(
                process_node=calculation_node
            )
          # logger.report(f'CALCULATION_DUMP_PATH: {calculation_dump_path}')

            with contextlib.suppress(FileExistsError):
                os.symlink(link_calculations_dir / calculation_node.uuid, calculation_dump_path)
