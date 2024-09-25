###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Functionality for dumping of a Collections of AiiDA ORMs."""

from __future__ import annotations

import logging
from collections import Counter
import os
from typing import List

from rich.pretty import pprint

from aiida import orm
from aiida.manage.configuration import Profile
from aiida.tools.dumping.abstract import AbstractDumper
from aiida.tools.dumping.data import DataDumper
from aiida.tools.dumping.process import ProcessDumper
from aiida.tools.dumping.utils import get_nodes_from_db
import itertools
import contextlib

LOGGER = logging.getLogger(__name__)
# TODO: Could also get the entities, or UUIDs directly, rather than just counting them here

DEFAULT_PROCESSES_TO_DUMP = [orm.CalculationNode, orm.WorkflowNode]
DEFAULT_DATA_TO_DUMP = [
    orm.StructureData,
    orm.Code,
    orm.Computer,
]
DEFAULT_ENTITIES_TO_DUMP = DEFAULT_PROCESSES_TO_DUMP + DEFAULT_DATA_TO_DUMP


class CollectionDumper(AbstractDumper):
    def __init__(
        self,
        # profile: Profile | None = None,
        qb_instance: orm.QueryBuilder | None = None,
        dump_processes: bool = False,
        dump_data: bool = False,
        link_processes: bool = False,
        link_data: bool = False,
        entities_to_dump: List | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        # self.profile = profile
        self.qb_instance = qb_instance
        self.dump_processes = dump_processes
        self.dump_data = dump_data
        self.link_processe = link_processes
        self.link_data = link_data

        if entities_to_dump is None:
            entities_to_dump = DEFAULT_ENTITIES_TO_DUMP
        self.entities_to_dump = entities_to_dump

        self.kwargs = kwargs

    @staticmethod
    def create_entity_counter():
        raise NotImplementedError('This should be implemented in subclasses.')

    @staticmethod
    def _obtain_calculations():
        raise NotImplementedError('This should be implemented in subclasses.')

    @staticmethod
    def _obtain_workflows():
        raise NotImplementedError('This should be implemented in subclasses.')

    # def dump(self):
    #     orm_entities = self._retrieve_orm_entities()

    #     for orm_entity in orm_entities:
    #         if isinstance(orm_entity, orm.ProcessNode):
    #             process_dumper = ProcessDumper(**self.kwargs)
    #             # process_dumper.pretty_print()
    #             print(process_dumper)
    #         elif isinstance(orm_entity, orm.Data):
    #             data_dumper = DataDumper(**self.kwargs)
    #         break

    def should_dump_calculations(self) -> bool:
        return (
            sum(
                self.entity_counter.get(orm_process_class, 0)
                for orm_process_class in [orm.CalcJobNode, orm.CalcFunctionNode]
            )
            > 0
        )

    def should_dump_workflows(self) -> bool:
        return (
            sum(
                self.entity_counter.get(orm_process_class, 0)
                for orm_process_class in [orm.WorkChainNode, orm.WorkFunctionNode]
            )
            > 0
        )

    def _dump_calculations_hidden(self, calculations):
        # ? Dump only top-level workchains, as that includes sub-workchains already

        for calculation in calculations:
            calculation_dumper = ProcessDumper(overwrite=self.overwrite)

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

    def _dump_link_workflows(self, workflows, link_calculations: bool = True):
        # workflow_nodes = get_nodes_from_db(aiida_node_type=orm.WorkflowNode, with_group=self.group, flat=True)
        for workflow in workflows:
            workflow_dumper = ProcessDumper(overwrite=True)

            link_calculations_dir = self.hidden_aiida_path / 'calculations'
            # TODO: If the GroupDumper is called from somewhere else outside, prefix the path with `groups/core` etc
            workflow_dump_path = (
                self.output_path
                / 'workflows'
                / workflow_dumper._generate_default_dump_path(process_node=workflow, prefix=None)
            )
            # logger.report(f'WORKFLOW_DUMP_PATH: {workflow_dump_path}')

            workflow_dumper._dump_workflow(
                workflow_node=workflow,
                output_path=workflow_dump_path,
                link_calculations=link_calculations,
                link_calculations_dir=link_calculations_dir,
            )

    def _link_calculations_hidden(self, calculations):
        # calculation_nodes = get_nodes_from_db(aiida_node_type=orm.CalculationNode, with_group=self.group, flat=True)
        for calculation_node in calculations:
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

    def _dump_data_hidden(self, data_nodes):
        # data_nodes = get_nodes_from_db(aiida_node_type=orm.Data, with_group=self.group, flat=True)
        for data_node in data_nodes:
            data_dump_path = self.hidden_aiida_path / 'data' / data_node.uuid
            data_dumper = DataDumper(overwrite=self.overwrite)
            data_dumper.pretty_print()

            try:
                data_dumper.dump(data_node=data_node, output_path=data_dump_path)
            except:
                # pass
                print(f'data_dumper.dump(data_node=data_node, output_path=data_dump_path{data_node, data_dump_path}')
                # pass
                raise
