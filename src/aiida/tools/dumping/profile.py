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

from collections.abc import Iterable
from typing import cast

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.manage import load_profile
from aiida.manage.configuration.profile import Profile
from aiida.tools.dumping.base import BaseDumper
from aiida.tools.dumping.collection import CollectionDumper
from aiida.tools.dumping.config import BaseDumpConfig, ProfileDumpConfig
from aiida.tools.dumping.logger import DumpLogger
from aiida.tools.dumping.process import ProcessDumper
from aiida.tools.dumping.utils import _filter_by_last_dump_time, _safe_delete_dir

logger = AIIDA_LOGGER.getChild('tools.dumping')

# TODO: If a Node is not created newly, but added to a newly created group, and the dumping is run, this is not picked
# up. No new nodes to dump are obtained.
# TODO: If a sub-workflow of another workflow is in its own group, this group is not created
# TODO:


class ProfileDumper(BaseDumper):
    """Class to handle dumping of the data of an AiiDA profile."""

    def __init__(
        self,
        profile: str | Profile | None = None,
        base_dump_config: BaseDumpConfig | None = None,
        dump_logger: DumpLogger | None = None,
        profile_dump_config: ProfileDumpConfig | None = None,
        process_dumper: ProcessDumper | None = None,
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

        super().__init__(base_dump_config=base_dump_config, dump_logger=dump_logger)

        self.groups = groups
        self.process_dumper = process_dumper or ProcessDumper()
        self.profile_dump_config = profile_dump_config or ProfileDumpConfig()

        self.should_dump_processes = self.profile_dump_config.dump_processes
        self.symlink_duplicates = self.profile_dump_config.symlink_duplicates
        self.delete_missing = self.profile_dump_config.delete_missing
        self.organize_by_groups = self.profile_dump_config.organize_by_groups
        self.only_top_level_calcs = self.profile_dump_config.only_top_level_calcs
        self.only_top_level_workflows = self.profile_dump_config.only_top_level_workflows

        if not isinstance(profile, Profile):
            profile = load_profile(profile=profile, allow_switch=True)
        self.profile = profile

        self._processes_to_dump: Iterable[str] | None = None
        self._processes_to_delete: Iterable[str] | None = None

    def _dump_processes_not_in_any_group(self):
        """Dump the profile's process data not contained in any group."""

        # `dump_parent_path` set to CWD in the `post_init` method of the `BaseDumper` dataclass if not given
        assert self.dump_parent_path is not None
        if self.organize_by_groups:
            output_path = self.dump_parent_path / 'no-group'
        else:
            output_path = self.dump_parent_path

        no_group_nodes = self._get_no_group_processes()

        self.base_dump_config.dump_parent_path = output_path

        no_group_dumper = CollectionDumper(
            group=None,
            collection_nodes=no_group_nodes,
            base_dump_config=self.base_dump_config,
            profile_dump_config=self.profile_dump_config,
            process_dumper=self.process_dumper,
            dump_logger=self.dump_logger,
        )

        # Add additional check here to only issue the message when there are actual processes to dump for a group
        # This might not be the case for, e.g., pseudopotential groups, or if there are no new processes since the
        # last dumping
        if self.should_dump_processes and not no_group_dumper.processes_to_dump.is_empty:
            logger.report(f'Dumping processes not in any group for profile `{self.profile.name}`...')

            no_group_dumper.dump()

    def _dump_processes_per_group(self, groups):
        # === Dump data per-group if Groups exist in profile or are selected ===

        assert self.dump_parent_path is not None

        for group in groups:
            if self.organize_by_groups:
                output_path = self.dump_parent_path / f'group-{group.label}'
            else:
                output_path = self.dump_parent_path

            # TODO: Find a better solution for this...
            self.base_dump_config.dump_parent_path = output_path

            group_dumper = CollectionDumper(
                base_dump_config=self.base_dump_config,
                profile_dump_config=self.profile_dump_config,
                process_dumper=self.process_dumper,
                dump_logger=self.dump_logger,
                group=group,
            )

            # Add additional check here to only issue the message when there are actual processes to dump for a group
            # This might not be the case for, e.g., pseudopotential groups, or if there are no new processes since the
            # last dumping
            # breakpoint()
            if self.should_dump_processes and not group_dumper.processes_to_dump.is_empty:
                # breakpoint()
                logger.report(f'Dumping processes in group {group.label} for profile `{self.profile.name}`...')

                group_dumper.dump()

    def _get_no_group_processes(self) -> Iterable[str]:
        """Obtain nodes in the profile that are not part of any group.

        :return: List of UUIDs of selected nodes.
        """

        profile_groups = cast(list[orm.Group], orm.QueryBuilder().append(orm.Group).all(flat=True))
        profile_processes = cast(
            Iterable[str], orm.QueryBuilder().append(orm.ProcessNode, project=['uuid']).all(flat=True)
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

        process_nodes: Iterable[str] = [
            profile_node for profile_node in profile_processes if profile_node not in nodes_in_groups
        ]
        process_nodes = _filter_by_last_dump_time(nodes=process_nodes, last_dump_time=self.last_dump_time)

        return process_nodes

    def dump_processes(self):
        # No groups selected, dump data which is not part of any group
        # If groups selected, however, this data should not also be dumped automatically
        # TODO: Maybe populate the `processes_to_dump` property here, even though I don't really need it, as I get the
        # TODO: nodes from the specified collection
        if not self.groups:
            self._dump_processes_not_in_any_group()

            # Still, even without selecting groups, by default, all profile data should be dumped
            # Thus, we obtain all groups in the profile here
            profile_groups = orm.QueryBuilder().append(orm.Group).all(flat=True)
            self._dump_processes_per_group(groups=profile_groups)

        else:
            self._dump_processes_per_group(groups=self.groups)

    @property
    def processes_to_dump(self) -> Iterable[str]:
        if self._processes_to_dump is None:
            self._processes_to_dump = self._get_processes_to_dump()
        return self._processes_to_dump

    def _get_processes_to_dump(self) -> Iterable[str]:
        if self.last_dump_time is not None:
            process_qb = orm.QueryBuilder().append(
                orm.ProcessNode, project=['uuid'], filters={'ctime': {'>': self.last_dump_time}}
            )
        else:
            process_qb = orm.QueryBuilder().append(orm.ProcessNode, project=['uuid'])

        profile_processes = cast(Iterable[str], process_qb.all(flat=True))

        return profile_processes

    @property
    def processes_to_delete(self) -> Iterable[str]:
        if self._processes_to_delete is None:
            self._processes_to_delete = self._get_processes_to_delete()
        return self._processes_to_delete

    def _get_processes_to_delete(self) -> Iterable[str]:
        dump_logger = self.dump_logger
        log = dump_logger.log

        # breakpoint()
        dumped_uuids = set(list(log.calculations.entries.keys()) + list(log.workflows.entries.keys()))
        # Cannot use QB here because, when node deleted, it's not in the DB anymore
        # dumped_processes: set[str] = set(cast(list[str], dumped_qb.all(flat=True)))

        # TODO: Possibly filter here since last dump time
        # TODO: But it is highly likely that the last dump command with deletion was run a while ago
        # TODO: So I cannot filter by last dump time, but should probably take the whole set
        profile_qb = orm.QueryBuilder().append(orm.ProcessNode)
        profile_processes = set(cast(Iterable[orm.ProcessNode], profile_qb.all(flat=True)))
        profile_uuids = set([process.uuid for process in profile_processes if process.caller is None])

        to_delete_uuids = list(dumped_uuids - profile_uuids)

        return to_delete_uuids

    def _delete_missing_node(self, to_delete_uuid) -> None:
        # TODO: Possibly make a delete method for the path and the log, and then call that in the loop

        dump_logger = self.dump_logger
        current_store = dump_logger.find_store_by_uuid(uuid=to_delete_uuid)
        if not current_store:
            return

        # ! Cannot load the node via its UUID here and use the type to get the correct store, as the Node is deleted
        # ! from the DB. Should find a better solution

        try:
            path_to_delete = current_store.entries[to_delete_uuid].path
            _safe_delete_dir(path_to_validate=path_to_delete, safeguard_file='.aiida_node_metadata.yaml', verbose=False)
            current_store.del_entry(uuid=to_delete_uuid)
        except:
            raise

    def delete_processes(self):
        to_dump_processes = self.processes_to_dump
        to_delete_processes = self.processes_to_delete

        print(f'TO_DUMP_PROCESSES: {to_dump_processes}')
        print(f'TO_DELETE_PROCESSES: {to_delete_processes}')

        # breakpoint()
        for to_delete_uuid in to_delete_processes:
            self._delete_missing_node(to_delete_uuid=to_delete_uuid)

        # TODO: Need to also delete entry from the log when I delete the dir
        # TODO: Add also logging for node/path deletion
