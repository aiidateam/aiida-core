###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

# TODO: Possibly use `batch_iter` from aiida.tools.archive.common

from __future__ import annotations

from typing import Sequence, cast

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.manage import load_profile
from aiida.manage.configuration.profile import Profile
from aiida.tools.dumping.base import BaseDumper
from aiida.tools.dumping.collection import CollectionDumper
from aiida.tools.dumping.config import ProfileDumpConfig
from aiida.tools.dumping.logger import DumpLogger
from aiida.tools.dumping.process import ProcessDumper
from aiida.tools.dumping.utils import filter_by_last_dump_time

logger = AIIDA_LOGGER.getChild('tools.dumping')


class ProfileDumper:
    """Class to handle dumping of the data of an AiiDA profile."""

    def __init__(
        self,
        profile: str | Profile | None = None,
        profile_dump_config: ProfileDumpConfig | None = None,
        base_dumper: BaseDumper | None = None,
        process_dumper: ProcessDumper | None = None,
        dump_logger: DumpLogger | None = None,
        # deduplicate: bool = True,
        groups: Sequence[str | orm.Group] | None = None,
    ):
        """Initialize the ProfileDumper.

        :param profile: The selected profile to dump.
        :param base_dumper: Base dumper instance or None (gets instantiated).
        :param process_dumper: Process dumper instance or None (gets instantiated).
        :param dump_logger: Logger for the dumping (gets instantiated).
        :param organize_by_groups: Organize dumped data by groups.
        :param groups: Dump data only for selected groups.
        :param dump_processes: Should dump process data?
        """

        self.groups = groups

        self.base_dumper = base_dumper or BaseDumper()
        self.process_dumper = process_dumper or ProcessDumper()
        self.dump_logger = dump_logger or DumpLogger(dump_parent_path=self.base_dumper.dump_parent_path)

        self.profile_dump_config = profile_dump_config or ProfileDumpConfig()

        if not isinstance(profile, Profile):
            profile = load_profile(profile=profile, allow_switch=True)
        self.profile = profile

    def _dump_processes_not_in_any_group(self):
        """Dump the profile's process data not contained in any group."""

        # `dump_parent_path` set to CWD in the `post_init` method of the `BaseDumper` dataclass if not given
        assert self.base_dumper.dump_parent_path is not None
        if self.profile_dump_config.organize_by_groups:
            output_path = self.base_dumper.dump_parent_path / 'no-group'
        else:
            output_path = self.base_dumper.dump_parent_path

        no_group_nodes = self._get_no_group_processes()

        no_group_dumper = CollectionDumper(
            collection=no_group_nodes,
            profile_dump_config=self.profile_dump_config,
            base_dumper=self.base_dumper,
            process_dumper=self.process_dumper,
            # deduplicate=self.deduplicate,
            dump_logger=self.dump_logger,
            output_path=output_path,
        )

        # Add additional check here to only issue the message when there are actual processes to dump for a group
        # This might not be the case for, e.g., pseudopotential groups, or if there are no new processes since the
        # last dumping
        if self.dump_processes and not no_group_dumper.processes_to_dump.is_empty:
            logger.report(f'Dumping processes not in any group for profile `{self.profile.name}`...')

            no_group_dumper.dump()

    def _dump_processes_per_group(self, groups):
        # === Dump data per-group if Groups exist in profile or are selected ===

        assert self.base_dumper.dump_parent_path is not None

        for group in groups:
            if self.profile_dump_config.organize_by_groups:
                output_path = self.base_dumper.dump_parent_path / f'group-{group.label}'
            else:
                output_path = self.base_dumper.dump_parent_path

            group_dumper = CollectionDumper(
                base_dumper=self.base_dumper,
                profile_dump_config=self.profile_dump_config,
                process_dumper=self.process_dumper,
                dump_logger=self.dump_logger,
                collection=group,
                # deduplicate=self.deduplicate,
                output_path=output_path,
            )

            # Add additional check here to only issue the message when there are actual processes to dump for a group
            # This might not be the case for, e.g., pseudopotential groups, or if there are no new processes since the
            # last dumping
            # breakpoint()
            if self.dump_processes and not group_dumper.processes_to_dump.is_empty:
                # breakpoint()
                logger.report(f'Dumping processes in group {group.label} for profile `{self.profile.name}`...')

                group_dumper.dump()

    def _get_no_group_processes(self) -> Sequence[str] | Sequence[int]:
        """Obtain nodes in the profile that are not part of any group.

        :return: List of UUIDs of selected nodes.
        """

        group_qb = orm.QueryBuilder().append(orm.Group)
        profile_groups = cast(Sequence[orm.Group], group_qb.all(flat=True))
        process_qb = orm.QueryBuilder().append(orm.ProcessNode, project=['uuid'])
        profile_nodes = cast(Sequence[str], process_qb.all(flat=True))

        nodes_in_groups: Sequence[str] = [node.uuid for group in profile_groups for node in group.nodes]

        # Need to expand here also with the called_descendants of `WorkflowNodes`, otherwise the called
        # `CalculationNode`s for `WorkflowNode`s that are part of a group are dumped twice
        # Get the called descendants of WorkflowNodes within the nodes_in_groups list
        sub_nodes_in_groups: Sequence[str] = [
            node.uuid
            for n in nodes_in_groups
            # if isinstance((workflow_node := orm.load_node(n)), orm.WorkflowNode)
            if isinstance((workflow_node := orm.load_node(n)), orm.ProcessNode)
            for node in workflow_node.called_descendants
        ]

        nodes_in_groups += sub_nodes_in_groups

        process_nodes: Sequence[str | int] = [
            profile_node for profile_node in profile_nodes if profile_node not in nodes_in_groups
        ]
        process_nodes = filter_by_last_dump_time(nodes=process_nodes, last_dump_time=self.base_dumper.last_dump_time)

        return process_nodes

    def dump_processes(self):
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

    @staticmethod
    def _get_number_of_nodes_to_dump(last_dump_time) -> dict[str, int]:
        result = {}
        for node_type in (orm.CalculationNode, orm.WorkflowNode):
            qb = orm.QueryBuilder().append(node_type, project=['uuid'])
            nodes = cast(Sequence[str], qb.all(flat=True))
            nodes = filter_by_last_dump_time(nodes=nodes, last_dump_time=last_dump_time)
            result[node_type.class_node_type.split('.')[-2] + 's'] = len(nodes)
        return result
