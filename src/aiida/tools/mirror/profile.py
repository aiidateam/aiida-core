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
# No groups selected, mirror data which is not part of any group
# If groups selected, however, this data should not also be mirrored automatically
# TODO: Maybe populate the `processes_to_mirror` property here, even though I don't really need it, as I get the
# TODO: nodes from the specified collection

from __future__ import annotations

import copy
import dataclasses
from datetime import datetime
from pathlib import Path
from typing import cast

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.manage import load_profile
from aiida.manage.configuration.profile import Profile
from aiida.tools.mirror.collection import BaseCollectionMirror
from aiida.tools.mirror.collector import MirrorNodeContainer
from aiida.tools.mirror.config import (
    GroupMirrorConfig,
    MirrorMode,
    NodeCollectorConfig,
    NodeMirrorGroupScope,
    ProcessMirrorConfig,
    ProfileMirrorConfig,
)
from aiida.tools.mirror.group import GroupMirror
from aiida.tools.mirror.logger import MirrorLog, MirrorLogger
from aiida.tools.mirror.utils import (
    MirrorPaths,
    generate_profile_default_mirror_path,
    load_given_group,
)

logger = AIIDA_LOGGER.getChild('tools.mirror.profile')


class ProfileMirror(BaseCollectionMirror):
    """Class to handle mirroring of the data of an AiiDA profile."""

    def __init__(
        self,
        profile: str | Profile | None = None,
        mirror_mode: MirrorMode = MirrorMode.INCREMENTAL,
        mirror_paths: MirrorPaths | None = None,
        last_mirror_time: datetime | None = None,
        mirror_logger: MirrorLogger | None = None,
        node_collector_config: NodeCollectorConfig | None = None,
        process_mirror_config: ProcessMirrorConfig | None = None,
        profile_mirror_config: ProfileMirrorConfig | None = None,
        groups: list[str] | list[orm.Group] | None = None,
    ):
        """Initialize the ProfileMirror.

        """

        if mirror_paths is None:
            default_mirror_path = generate_profile_default_mirror_path()
            mirror_paths = MirrorPaths(parent=Path.cwd(), child=default_mirror_path)

        super().__init__(
            mirror_mode=mirror_mode,
            mirror_paths=mirror_paths,
            last_mirror_time=last_mirror_time,
            mirror_logger=mirror_logger,
            node_collector_config=node_collector_config,
        )

        if not isinstance(profile, Profile):
            profile: Profile = load_profile(profile=profile, allow_switch=True)
        self.profile = profile

        if groups is not None:
            self.groups = [load_given_group(group=g) for g in groups]
        else:
            self.groups = []

        self.process_mirror_config = process_mirror_config or ProcessMirrorConfig()
        self.profile_mirror_config = profile_mirror_config or ProfileMirrorConfig()

        # Construct `GroupMirrorConfig` from options passed via `ProfileMirrorConfig`
        # The arguments of `GroupMirrorConfig` are a subset of `ProfileMirrorConfig`
        self.group_mirror_config = GroupMirrorConfig(
            **{
                field.name: getattr(self.profile_mirror_config, field.name)
                for field in dataclasses.fields(class_or_instance=GroupMirrorConfig)
            }
        )

        # Unpack arguments for easier access
        self.symlink_duplicates = self.profile_mirror_config.symlink_duplicates
        self.delete_missing = self.profile_mirror_config.delete_missing
        self.organize_by_groups = self.profile_mirror_config.organize_by_groups
        self.only_groups = self.profile_mirror_config.only_groups

        # self.group_container_mapping: dict[orm.Group, MirrorNodeContainer] = {}

    def _mirror_per_group(self, groups: list[orm.Group]) -> None:
        """Iterate through a list of groups and mirror the contained processes in their dedicated directories.

        :param groups: List of ``orm.Group`` entities.
        """

        group_store = self.mirror_logger.groups

        for group in groups:
            if self.organize_by_groups:
                group_subpath = 'groups' / GroupMirror.get_group_subpath(group=group)
            else:
                group_subpath = Path('.')

            mirror_paths_group = MirrorPaths(parent=self.mirror_paths.absolute, child=group_subpath)

            group_mirrorer = GroupMirror(
                group=group,
                mirror_paths=mirror_paths_group,
                mirror_mode=self.mirror_mode,
                process_mirror_config=self.process_mirror_config,
                group_mirror_config=self.group_mirror_config,
                mirror_logger=self.mirror_logger,
            )

            msg = f'Mirroring processes in group `{group.label}` for profile `{self.profile.name}`...'
            logger.report(msg)

            group_mirrorer.do_mirror()

            group_store.add_entry(
                uuid=group.uuid,
                entry=MirrorLog(
                    path=mirror_paths_group.absolute,
                    time=datetime.now().astimezone(),
                ),
            )

    def _mirror_not_in_any_group(self) -> None:
        """Mirror the profile's process data not contained in any group."""

        if self.organize_by_groups:
            no_group_subpath = Path('no-group')
        else:
            no_group_subpath = Path('.')

        mirror_paths_group = MirrorPaths(
            parent=self.mirror_paths.parent / self.mirror_paths.child, child=no_group_subpath
        )

        # See here how to append to the parent and child of MirrorPaths
        node_collector_config_no_group = copy.deepcopy(self.node_collector_config)
        node_collector_config_no_group.group_scope = NodeMirrorGroupScope.NO_GROUP

        no_group_mirrorer = GroupMirror(
            mirror_paths=mirror_paths_group,
            group=None,
            mirror_mode=self.mirror_mode,
            process_mirror_config=self.process_mirror_config,
            group_mirror_config=self.group_mirror_config,
            mirror_logger=self.mirror_logger,
            node_collector_config=node_collector_config_no_group,
        )

        msg = f'Mirroring processes not in any group for profile `{self.profile.name}`...'
        logger.report(msg)
        no_group_mirrorer.no_group_mirror()
        # TODO: Possibly add entry to logger

    def do_mirror(self):
        """_summary_

        :param
        """
        self._pre_mirror()

        # If `groups` given on construction, mirror only data within those groups
        if self.groups:
            self._mirror_per_group(groups=self.groups)

        # If `groups` given on construction, mirror only data within those groups
        else:
            if not self.only_groups:
                self._mirror_not_in_any_group()

            # Still, even without selecting groups, by default, all profile data should be mirrored
            # Thus, we obtain all groups in the profile here
            profile_groups = cast(list[orm.Group], orm.QueryBuilder().append(orm.Group).all(flat=True))
            self._mirror_per_group(groups=profile_groups)

        # if delete_missing_processes:
        #     if num_processes_to_delete == 0:
        #         msg = 'No processes to delete.'
        #         logger.report(msg)
        #     else:
        #         self.delete_processes()
        #         msg = f'Deleted {num_processes_to_delete} node directories.'
        #         logger.report(msg)

        # if num_groups_to_delete == 0:
        #     echo.echo_success('No groups to delete.')
        # else:
        #     self.delete_groups()
        #     echo.echo_success(f'Deleted {num_groups_to_delete} group directories.')

        # if update_groups:
        #     relabeled_paths = self.update_groups()
        #     msg = 'Renamed group directories and updated the log file.'
        #     echo.echo_success(msg)
        #     # print(relabeled_paths)

        self._post_mirror()


#####

# def _mirror_by_groups(self):
# import ipdb; ipdb.set_trace()

# @cached_property
# def processes_to_mirror(self) -> list[str]:
#     return self._get_processes_to_mirror()

# def _get_processes_to_mirror(self) -> list[str]:
#     if self.last_mirror_time is not None:
#         process_qb = orm.QueryBuilder().append(
#             orm.ProcessNode,
#             project=['uuid'],
#             filters={'ctime': {'>': self.last_mirror_time}},
#         )
#     else:
#         process_qb = orm.QueryBuilder().append(orm.ProcessNode, project=['uuid'])

#     profile_processes = cast(list[str], process_qb.all(flat=True))

#     return profile_processes

# @cached_property
# def groups_to_delete(self) -> list[str]:
#     if not self.delete_missing:
#         return []
#     if self._groups_to_delete is None:
#         self._groups_to_delete = self._get_groups_to_delete()
#     return self._groups_to_delete

# def _get_groups_to_delete(self) -> list[str]:
#     breakpoint()
#     mirror_logger = self.mirror_logger
#     log = mirror_logger.log

#     # Cannot use QB here because, when node deleted, it's not in the DB anymore
#     mirrored_uuids = set(list(log.groups.entries.keys()))

#     profile_uuids = cast(
#         set[str],
#         set(orm.QueryBuilder().append(orm.Group, project=['uuid']).all(flat=True)),
#     )

#     to_delete_uuids = list(mirrored_uuids - profile_uuids)

#     return to_delete_uuids

# # TODO: Also move this into a more general method that returns a `NodeContainer`
# @cached_property
# def processes_to_delete(self) -> list[str]:
#     if not self.delete_missing:
#         return []
#     if self._processes_to_delete is None:
#         self._processes_to_delete = self._get_processes_to_delete()
#     return self._processes_to_delete

# def _get_processes_to_delete(self) -> list[str]:
#     mirror_logger = self.mirror_logger
#     log = mirror_logger.log

#     # Cannot use QB here because, when node deleted, it's not in the DB anymore
#     mirrored_uuids = set(list(log.calculations.entries.keys()) + list(log.workflows.entries.keys()))

#     # One could possibly filter here since last mirror time, however
#     # it is highly likely that the last mirror command with deletion was run a while ago
#     # So I cannot filter by last mirror time, but should probably take the whole set
#     profile_uuids = cast(
#         set[str],
#         set(orm.QueryBuilder().append(orm.ProcessNode, project=['uuid']).all(flat=True)),
#     )
#     # Don't restrict here to only top-level processes, as all file paths, also for sub-processes are actually
#     # created and stored in the log
#     # profile_uuids = set([process.uuid for process in profile_processes if process.caller is None])

#     to_delete_uuids = list(mirrored_uuids - profile_uuids)

#     return to_delete_uuids

# def delete_processes(self):
#     # to_mirror_processes = self.processes_to_mirror
#     to_delete_processes = self.processes_to_delete

#     # print(f'TO_MIRROR_PROCESSES: {to_mirror_processes}')
#     # print(f'TO_DELETE_PROCESSES: {to_delete_processes}')

#     for to_delete_uuid in to_delete_processes:
#         delete_missing_node_dir(mirror_logger=self.mirror_logger, to_delete_uuid=to_delete_uuid)

#     # TODO: Add also logging for node/path deletion?

# def delete_groups(self):
#     to_delete_groups = self.groups_to_delete
#     for to_delete_uuid in to_delete_groups:
#         self._delete_missing_node_dir(to_delete_uuid=to_delete_uuid)
#         # ! Problem: Don't have safeguard file in empty group directory

# def update_groups(self) -> list[dict[str, Path]]:
#     mirror_logger = self.mirror_logger

#     # Order is the same as in the mirroring log file -> Not using a profile QB here
#     # Also, if the group is new (and contains new nodes), it will be mirrored anyway
#     mirrored_group_uuids = list(mirror_logger.groups.entries.keys())

#     old_mapping: dict[str, Path] = dict(
#         zip(
#             mirrored_group_uuids,
#             [p.path for p in mirror_logger.groups.entries.values()],
#         )
#     )

#     new_mapping: dict[str, Path] = dict(
#         zip(
#             mirrored_group_uuids,
#             [self.mirror_parent_path / 'groups' / get_group_subpath(orm.load_group(g)) for g in mirrored_group_uuids],
#         )
#     )

#     modified_paths: list[dict[str, Path]] = []

#     for uuid, old_path in old_mapping.items():
#         new_path = new_mapping.get(uuid)

#         if new_path and old_path != new_path:
#             # logger.report(f'Renaming {old_path} -> {new_path}')
#             old_path.rename(new_path)
#             try:
#                 mirror_logger.groups.entries[uuid].path = new_path
#             except:
#                 # import ipdb, ipdb.set_trace()
#                 raise

#             modified_paths.append(
#                 {
#                     'old': old_path,
#                     'new': new_path,
#                 }
#             )

#     return modified_paths
