###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

# TODO: Possibly use `batch_iter` from aiida.tools.archive.common
# TODO: Add option to just print the resulting directory tree

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import cast

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.manage import load_profile
from aiida.manage.configuration.profile import Profile
from aiida.tools.dumping.base import BaseDumper
from aiida.tools.dumping.collection import CollectionDumper
from aiida.tools.dumping.config import (
    BaseDumpConfig,
    ProcessDumpConfig,
    ProfileDumpConfig,
)
from aiida.tools.dumping.logger import DumpLog, DumpLogger
from aiida.tools.dumping.utils import (
    delete_missing_node_dir,
    filter_nodes_last_dump_time,
    get_group_subpath,
    load_given_group,
)

logger = AIIDA_LOGGER.getChild('tools.dumping')

# TODO: Use ProcessContainer rather than list[str]


class ProfileDumper(BaseDumper):
    """Class to handle dumping of the data of an AiiDA profile."""

    def __init__(
        self,
        profile: str | Profile | None = None,
        dump_parent_path: Path | None = None,
        dump_sub_path: Path | None = None,
        last_dump_time: datetime | None = None,
        dump_logger: DumpLogger | None = None,
        base_dump_config: BaseDumpConfig | None = None,
        process_dump_config: ProcessDumpConfig | None = None,
        profile_dump_config: ProfileDumpConfig | None = None,
        groups: list[str] | list[orm.Group] | None = None,
    ):
        """Initialize the ProfileDumper.

        :param profile: The selected profile to dump.
        :param base_dump_config: Base dumper instance or None (gets instantiated).
        :param process_dumper: Process dumper instance or None (gets instantiated).
        :param dump_logger: Logger for the dumping (gets instantiated).
        :param organize_by_groups: Organize dumped data by groups.
        :param groups: Dump data only for selected groups.
        """

        super().__init__(
            dump_parent_path=dump_parent_path,
            dump_sub_path=dump_sub_path,
            last_dump_time=last_dump_time,
            base_dump_config=base_dump_config,
            dump_logger=dump_logger,
        )

        if groups is not None:
            self.groups = [load_given_group(group=g) for g in groups]
        else:
            self.groups = []

        self.base_dump_config = base_dump_config or BaseDumpConfig()
        self.process_dump_config = process_dump_config or ProcessDumpConfig()
        self.profile_dump_config = profile_dump_config or ProfileDumpConfig()

        # Unpack arguments for easier access
        self.should_dump_processes = self.profile_dump_config.dump_processes
        self.symlink_duplicates = self.profile_dump_config.symlink_duplicates
        self.delete_missing = self.profile_dump_config.delete_missing
        self.organize_by_groups = self.profile_dump_config.organize_by_groups
        self.only_groups = self.profile_dump_config.only_groups
        self.only_top_level_calcs = self.profile_dump_config.only_top_level_calcs
        self.only_top_level_workflows = self.profile_dump_config.only_top_level_workflows

        if not isinstance(profile, Profile):
            profile = load_profile(profile=profile, allow_switch=True)
        self.profile = profile

        self._processes_to_dump: list[str] | None = None
        self._processes_to_delete: list[str] | None = None

        # self._groups_to_dump: list[str] | None = None
        self._groups_to_delete: list[str] | None = None

    def _dump_processes_not_in_any_group(self) -> None:
        """Dump the profile's process data not contained in any group."""

        if self.organize_by_groups:
            no_group_subpath = Path('no-group')
        else:
            no_group_subpath = Path('.')

        no_group_output_path = self.dump_parent_path / self.dump_sub_path / no_group_subpath

        no_group_nodes = self._get_no_group_processes()
        no_group_dumper = CollectionDumper(
            dump_parent_path=self.dump_parent_path / self.dump_sub_path,
            dump_sub_path=no_group_subpath,
            group=None,
            collection_nodes=no_group_nodes,
            base_dump_config=self.base_dump_config,
            process_dump_config=self.process_dump_config,
            profile_dump_config=self.profile_dump_config,
            dump_logger=self.dump_logger,
        )

        if self.should_dump_processes and not no_group_dumper.processes_to_dump.is_empty:
            msg = f'Dumping processes not in any group for profile `{self.profile.name}`...'
            logger.report(msg)
            no_group_dumper.dump()
            # TODO: Possibly add entry to logger

    def _dump_processes_per_group(self, groups: list[orm.Group]) -> None:
        """Iterate through a list of groups and dump the contained processes in their dedicated directories.

        :param groups: List of ``orm.Group`` entities.
        """

        group_store = self.dump_logger.groups

        for group in groups:
            if self.organize_by_groups:
                group_subpath = 'groups' / get_group_subpath(group=group)
            else:
                group_subpath = Path('.')

            group_dumper = CollectionDumper(
                dump_parent_path=self.dump_parent_path / self.dump_sub_path,
                dump_sub_path=group_subpath,
                base_dump_config=self.base_dump_config,
                process_dump_config=self.process_dump_config,
                profile_dump_config=self.profile_dump_config,
                dump_logger=self.dump_logger,
                group=group,
            )
            # ipdb.set_trace()
            # FIXME: Hack for now...
            # self.processes

            if self.should_dump_processes and not group_dumper.processes_to_dump.is_empty:
                msg = f'Dumping processes in group `{group.label}` for profile `{self.profile.name}`...'
                logger.report(msg)
                group_dumper.dump()

                group_output_path = self.dump_parent_path / self.dump_sub_path / group_subpath
                group_store.add_entry(
                    uuid=group.uuid,
                    entry=DumpLog(
                        path=group_output_path,
                        time=datetime.now().astimezone(),
                    ),
                )

    def _get_no_group_processes(self) -> list[str]:
        """Obtain nodes in the profile that are not part of any group.

        :return: List of UUIDs of selected nodes.
        """

        profile_groups = cast(list[orm.Group], orm.QueryBuilder().append(orm.Group).all(flat=True))
        profile_processes = cast(
            list[str],
            orm.QueryBuilder().append(orm.ProcessNode, project=['uuid']).all(flat=True),
        )

        nodes_in_groups: list[str] = [node.uuid for group in profile_groups for node in group.nodes]

        # Need to expand here also with the called_descendants of `WorkflowNodes`, otherwise the called
        # `CalculationNode`s for `WorkflowNode`s that are part of a group are dumped twice
        # Get the called descendants of WorkflowNodes within the nodes_in_groups list
        sub_nodes_in_groups: list[str] = [
            node.uuid
            for n in nodes_in_groups
            # if isinstance((workflow_node := orm.load_node(n)), orm.WorkflowNode)
            if isinstance((workflow_node := orm.load_node(n)), orm.ProcessNode)
            for node in workflow_node.called_descendants
        ]

        nodes_in_groups += sub_nodes_in_groups

        process_nodes: list[str] = [
            profile_node for profile_node in profile_processes if profile_node not in nodes_in_groups
        ]
        process_nodes = filter_nodes_last_dump_time(nodes=process_nodes, last_dump_time=self.last_dump_time)

        return process_nodes

    def dump_processes(self):
        # No groups selected, dump data which is not part of any group
        # If groups selected, however, this data should not also be dumped automatically
        # TODO: Maybe populate the `processes_to_dump` property here, even though I don't really need it, as I get the
        # TODO: nodes from the specified collection

        if not self.groups:
            if not self.only_groups:
                self._dump_processes_not_in_any_group()

            # Still, even without selecting groups, by default, all profile data should be dumped
            # Thus, we obtain all groups in the profile here
            profile_groups = cast(list[orm.Group], orm.QueryBuilder().append(orm.Group).all(flat=True))
            self._dump_processes_per_group(groups=profile_groups)

        else:
            self._dump_processes_per_group(groups=[g for g in self.groups if g is not None])

    @property
    def processes_to_dump(self) -> list[str]:
        if self._processes_to_dump is None:
            self._processes_to_dump = self._get_processes_to_dump()
        return self._processes_to_dump

    def _get_processes_to_dump(self) -> list[str]:
        if self.last_dump_time is not None:
            process_qb = orm.QueryBuilder().append(
                orm.ProcessNode,
                project=['uuid'],
                filters={'ctime': {'>': self.last_dump_time}},
            )
        else:
            process_qb = orm.QueryBuilder().append(orm.ProcessNode, project=['uuid'])

        profile_processes = cast(list[str], process_qb.all(flat=True))

        return profile_processes

    @property
    def groups_to_delete(self) -> list[str]:
        if not self.delete_missing:
            return []
        if self._groups_to_delete is None:
            self._groups_to_delete = self._get_groups_to_delete()
        return self._groups_to_delete

    def _get_groups_to_delete(self) -> list[str]:
        breakpoint()
        dump_logger = self.dump_logger
        log = dump_logger.log

        # Cannot use QB here because, when node deleted, it's not in the DB anymore
        dumped_uuids = set(list(log.groups.entries.keys()))

        profile_uuids = cast(
            set[str],
            set(orm.QueryBuilder().append(orm.Group, project=['uuid']).all(flat=True)),
        )

        to_delete_uuids = list(dumped_uuids - profile_uuids)

        return to_delete_uuids

    @property
    def processes_to_delete(self) -> list[str]:
        if not self.delete_missing:
            return []
        if self._processes_to_delete is None:
            self._processes_to_delete = self._get_processes_to_delete()
        return self._processes_to_delete

    def _get_processes_to_delete(self) -> list[str]:
        dump_logger = self.dump_logger
        log = dump_logger.log

        # Cannot use QB here because, when node deleted, it's not in the DB anymore
        dumped_uuids = set(list(log.calculations.entries.keys()) + list(log.workflows.entries.keys()))

        # One could possibly filter here since last dump time, however
        # it is highly likely that the last dump command with deletion was run a while ago
        # So I cannot filter by last dump time, but should probably take the whole set
        profile_uuids = cast(
            set[str],
            set(orm.QueryBuilder().append(orm.ProcessNode, project=['uuid']).all(flat=True)),
        )
        # Don't restrict here to only top-level processes, as all file paths, also for sub-processes are actually
        # created and stored in the log
        # profile_uuids = set([process.uuid for process in profile_processes if process.caller is None])

        to_delete_uuids = list(dumped_uuids - profile_uuids)

        return to_delete_uuids

    def delete_processes(self):
        # to_dump_processes = self.processes_to_dump
        to_delete_processes = self.processes_to_delete

        # print(f'TO_DUMP_PROCESSES: {to_dump_processes}')
        # print(f'TO_DELETE_PROCESSES: {to_delete_processes}')

        for to_delete_uuid in to_delete_processes:
            delete_missing_node_dir(dump_logger=self.dump_logger, to_delete_uuid=to_delete_uuid)

        # TODO: Add also logging for node/path deletion?

    def delete_groups(self):
        to_delete_groups = self.groups_to_delete
        for to_delete_uuid in to_delete_groups:
            self._delete_missing_node_dir(to_delete_uuid=to_delete_uuid)
            # ! Problem: Don't have safeguard file in empty group directory

    def update_groups(self) -> list[dict[str, Path]]:
        dump_logger = self.dump_logger

        # Order is the same as in the mirroring log file -> Not using a profile QB here
        # Also, if the group is new (and contains new nodes), it will be dumped anyway
        dumped_group_uuids = list(dump_logger.groups.entries.keys())

        old_mapping: dict[str, Path] = dict(
            zip(
                dumped_group_uuids,
                [p.path for p in dump_logger.groups.entries.values()],
            )
        )

        new_mapping: dict[str, Path] = dict(
            zip(
                dumped_group_uuids,
                [self.dump_parent_path / 'groups' / get_group_subpath(orm.load_group(g)) for g in dumped_group_uuids],
            )
        )

        modified_paths: list[dict[str, Path]] = []

        for uuid, old_path in old_mapping.items():
            new_path = new_mapping.get(uuid)

            if new_path and old_path != new_path:
                # logger.report(f'Renaming {old_path} -> {new_path}')
                old_path.rename(new_path)
                try:
                    dump_logger.groups.entries[uuid].path = new_path
                except:
                    # For debugging
                    # import ipdb

                    raise

                modified_paths.append(
                    {
                        'old': old_path,
                        'new': new_path,
                    }
                )

        return modified_paths
