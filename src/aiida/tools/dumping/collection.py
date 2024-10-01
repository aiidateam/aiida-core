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
from aiida.cmdline.commands.cmd_data.cmd_export import data_export
import contextlib
from pathlib import Path
from aiida.common import timezone

logger = logging.getLogger(__name__)
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
        qb_instance: orm.QueryBuilder | None = None,
        should_dump_processes: bool = False,
        should_dump_data: bool = False,
        link_processes: bool = False,
        link_data: bool = False,
        entities_to_dump: List | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        # self.profile = profile
        self.qb_instance = qb_instance
        self.should_dump_processes = should_dump_processes
        self.should_dump_data = should_dump_data
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
            data_dump_path = self.hidden_aiida_path / 'data'
            data_dump_path.mkdir(exist_ok=True, parents=True)
            data_dumper = DataDumper(overwrite=self.overwrite)
            # data_dumper.pretty_print()

            try:
                # Must pass them implicitly here, rather than, e.g. `data_node=data_node`
                # Otherwise `singledispatch` raises: `IndexError: tuple index out of range`
                data_dumper.dump(data_node, data_dump_path)
            except:
                # pass
                print(f'data_dumper.dump(data_node=data_node, output_path=data_dump_path{data_node, data_dump_path}')
                # pass
                raise
