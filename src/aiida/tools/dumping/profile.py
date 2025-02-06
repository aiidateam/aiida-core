###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

# TODO: Use `batch_iter` from aiida.tools.archive.common

from __future__ import annotations

from typing import cast

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.manage import get_manager, load_profile
from aiida.manage.configuration.profile import Profile
from aiida.tools.dumping.base import BaseDumper
from aiida.tools.dumping.collection import CollectionDumper
from aiida.tools.dumping.logger import DumpLogger
from aiida.tools.dumping.process import ProcessDumper
from aiida.tools.dumping.utils import filter_by_last_dump_time

logger = AIIDA_LOGGER.getChild('tools.dumping')


class ProfileDumper:
    def __init__(
        self,
        profile: str | Profile | None = None,
        base_dumper: BaseDumper | None = None,
        process_dumper: ProcessDumper | None = None,
        dump_logger: DumpLogger | None = None,
        organize_by_groups: bool = True,
        deduplicate: bool = True,
        groups: list[str | orm.Group] | None = None,
        dump_processes: bool = True,
    ):
        self.organize_by_groups = organize_by_groups
        self.deduplicate = deduplicate
        self.dump_processes = dump_processes
        self.groups = groups

        self.base_dumper = base_dumper or BaseDumper()
        self.process_dumper = process_dumper or ProcessDumper()
        self.dump_logger = dump_logger or DumpLogger(dump_parent_path=self.base_dumper.dump_parent_path)

        # Load the profile
        if isinstance(profile, str):
            profile = load_profile(profile)

        if profile is None:
            manager = get_manager()
            profile = manager.get_profile()

        assert profile is not None
        self.profile = profile

    def dump(self):
        # No groups selected, dump data which is not part of any group
        # If groups selected, however, this data should not also be dumped automatically
        if not self.groups:
            self._dump_processes_not_in_any_group()

            # Still, even without selecting groups, by default, all profile data should be dumped
            # Thus, we obtain all groups in the profile here
            profile_groups = orm.QueryBuilder().append(orm.Group).all(flat=True)
            self._dump_processes_per_group(groups=profile_groups)

        else:
            self._dump_processes_per_group(groups=self.groups)

    def _dump_processes_not_in_any_group(self):
        # === Dump the data that is not associated with any group ===

        # `dump_parent_path` is set in the `post_init` method of the `BaseDumper` dataclass
        assert self.base_dumper.dump_parent_path is not None
        if self.organize_by_groups:
            output_path = self.base_dumper.dump_parent_path / 'no-group'
        else:
            output_path = self.base_dumper.dump_parent_path

        no_group_nodes = self._get_no_group_nodes()

        no_group_dumper = CollectionDumper(
            base_dumper=self.base_dumper,
            process_dumper=self.process_dumper,
            collection=no_group_nodes,
            deduplicate=self.deduplicate,
            dump_logger=self.dump_logger,
            output_path=output_path,
        )

        if self.dump_processes and no_group_dumper.should_dump_processes():
            logger.report(f'Dumping processes not in any group for profile `{self.profile.name}`...')

            no_group_dumper.dump()

    def _dump_processes_per_group(self, groups):
        # === Dump data per-group if Groups exist in profile or are selected ===

        for group in groups:
            if self.organize_by_groups:
                output_path = self.base_dumper.dump_parent_path / group.label
            else:
                output_path = self.base_dumper.dump_parent_path

            group_dumper = CollectionDumper(
                base_dumper=self.base_dumper,
                process_dumper=self.process_dumper,
                dump_logger=self.dump_logger,
                collection=group,
                deduplicate=self.deduplicate,
                output_path=output_path,
            )

            if self.dump_processes and group_dumper.should_dump_processes():
                logger.report(f'Dumping processes in group {group.label} for profile `{self.profile.name}`...')

                group_dumper.dump()

    def _get_no_group_nodes(self) -> list[str]:
        # Get all nodes that are _not_ in any group
        group_qb = orm.QueryBuilder().append(orm.Group)
        profile_groups = cast(list[orm.Group], group_qb.all(flat=True))
        node_qb = orm.QueryBuilder().append(orm.Node, project=['uuid'])
        profile_nodes = cast(list[str], node_qb.all(flat=True))

        nodes_in_groups: list[str] = [node.uuid for group in profile_groups for node in group.nodes]

        # Need to expand here also with the called_descendants of `WorkflowNodes`, otherwise the called
        # `CalculationNode`s for `WorkflowNode`s that are part of a group are dumped twice
        # Get the called descendants of WorkflowNodes within the nodes_in_groups list

        sub_nodes_in_groups: list[str] = [
            node.uuid
            for n in nodes_in_groups
            if isinstance((workflow_node := orm.load_node(n)), orm.WorkflowNode)
            for node in workflow_node.called_descendants
        ]

        # sub_nodes_in_groups: list[str] = [node.uuid for node in sub_nodes_in_groups]
        nodes_in_groups += sub_nodes_in_groups

        nodes: list[str] = [profile_node for profile_node in profile_nodes if profile_node not in nodes_in_groups]
        nodes = filter_by_last_dump_time(nodes=nodes, last_dump_time=self.base_dumper.last_dump_time)

        return nodes

    @staticmethod
    def _get_number_of_nodes_to_dump(last_dump_time) -> dict[str, int]:
        result = {}
        for node_type in (orm.CalculationNode, orm.WorkflowNode):
            qb = orm.QueryBuilder().append(node_type, project=['uuid'])
            nodes = cast(list[str], qb.all(flat=True))
            nodes = filter_by_last_dump_time(nodes=nodes, last_dump_time=last_dump_time)
            result[node_type.class_node_type.split('.')[-2] + 's'] = len(nodes)
        return result
