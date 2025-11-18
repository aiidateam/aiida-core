###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Class to collect nodes for dump feature."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type, Union, cast

import click

from aiida import orm
from aiida.common import AIIDA_LOGGER
from aiida.common.progress_reporter import get_progress_reporter, set_progress_bar_tqdm
from aiida.common.utils import DEFAULT_FILTER_SIZE, batch_iter
from aiida.tools._dumping.config import GroupDumpConfig, GroupDumpScope, ProfileDumpConfig
from aiida.tools._dumping.mapping import GroupNodeMapping
from aiida.tools._dumping.utils import (
    DUMP_PROGRESS_BAR_FORMAT,
    REGISTRY_TO_ORM_TYPE,
    DumpPaths,
    DumpTimes,
    GroupChanges,
    GroupInfo,
    GroupRenameInfo,
    NodeChanges,
    NodeMembershipChange,
    ProcessingQueue,
    RegistryNameType,
)

if TYPE_CHECKING:
    from aiida.tools._dumping.tracking import DumpTracker


__all__ = ('DumpChangeDetector',)

logger = AIIDA_LOGGER.getChild('tools._dumping.detect')


class DumpChangeDetector:
    """Detects changes in the database since the last dump."""

    NODE_TAG = 'node'
    GROUP_TAG = 'group_filter'
    USER_TAG = 'user_filter'
    COMPUTER_TAG = 'computer_filter'
    CODE_TAG = 'code_filter'

    def __init__(
        self,
        config: Union[GroupDumpConfig, ProfileDumpConfig],
        dump_tracker: DumpTracker,
        dump_paths: DumpPaths,
        dump_times: DumpTimes,
        current_mapping: GroupNodeMapping,
    ) -> None:
        """Initializes the DumpChangeDetector."""
        self.config: Union[GroupDumpConfig, ProfileDumpConfig] = config
        self.dump_tracker: DumpTracker = dump_tracker
        self.dump_paths: DumpPaths = dump_paths
        self.dump_times: DumpTimes = dump_times
        self._current_mapping: GroupNodeMapping = current_mapping
        self._grouped_node_uuids_cache: Optional[set[str]] = None

    @property
    def grouped_node_uuids(self) -> set[str]:
        """Cached property holding the set of UUIDs for all nodes in any group."""
        if self._grouped_node_uuids_cache is not None:
            return self._grouped_node_uuids_cache

        # Always use the provided mapping - no fallback!
        uuids = set().union(*self._current_mapping.group_to_nodes.values())
        self._grouped_node_uuids_cache = uuids
        return uuids

    def get_nodes(
        self,
        group_scope: GroupDumpScope = GroupDumpScope.ANY,
        group: Optional[orm.Group] = None,
        apply_filters: bool = True,
        ignore_time_filters: bool = False,
        exclude_tracked: bool = True,
    ) -> ProcessingQueue:
        """Unified method to get nodes with various filtering options.

        :param group_scope: Determines the query scope (ANY, IN_GROUP, NO_GROUP)
        :param group: The specific group to filter by when scope is IN_GROUP
        :param apply_filters: Whether to apply top-level and caller filters
        :param ignore_time_filters: Whether to ignore time-based filters
        :param exclude_tracked: Whether to exclude nodes already in dump tracker
        :return: ProcessingQueue containing the filtered nodes
        """

        if group_scope == GroupDumpScope.IN_GROUP and not group:
            msg = 'Scope is IN_GROUP but no group object was provided.'
            raise ValueError(msg)

        # Build base filters
        base_filters = {}
        if not ignore_time_filters and isinstance(self.config, (GroupDumpConfig, ProfileDumpConfig)):
            base_filters['mtime'] = self._resolve_time_filters()

        # Get nodes by type
        processing_queue = ProcessingQueue()

        # Process calculations
        logger.report('Querying calculation nodes from database...')
        calc_nodes = self._query_single_type(
            orm_type=orm.CalculationNode, group_scope=group_scope, group=group, base_filters=base_filters
        )
        logger.report(f'Retrieved {len(calc_nodes)} calculation nodes.')

        if exclude_tracked:
            calc_nodes = self._exclude_tracked_nodes(calc_nodes, 'calculations')
        if apply_filters:
            calc_nodes = self._apply_behavioral_filters(calc_nodes, 'calculations')
        processing_queue.calculations = calc_nodes

        # Process workflows
        logger.report('Querying workflow nodes from database...')
        workflow_nodes = self._query_single_type(
            orm_type=orm.WorkflowNode, group_scope=group_scope, group=group, base_filters=base_filters
        )
        logger.report(f'Retrieved {len(workflow_nodes)} workflow nodes.')

        if exclude_tracked:
            workflow_nodes = self._exclude_tracked_nodes(workflow_nodes, 'workflows')
        if apply_filters:
            workflow_nodes = self._apply_behavioral_filters(workflow_nodes, 'workflows')
        processing_queue.workflows = workflow_nodes

        return processing_queue

    def _query_single_type(
        self,
        orm_type: Type[orm.ProcessNode],
        group_scope: GroupDumpScope,
        group: Optional[orm.Group],
        base_filters: Dict[str, Any],
    ) -> List[orm.ProcessNode]:
        """Query nodes of a single ORM type with the given scope and filters.

        :param orm_type: AiiDA ``orm.ProcessNode`` type
        :param group_scope: Determines the query scope (ANY, IN_GROUP, NO_GROUP)
        :param group: The specific group to filter by when scope is IN_GROUP
        :param base_filters: Pre-specified filters
        :return: List of ``orm.ProcessNode`` instances obtained via the DB query
        """
        filters = base_filters.copy()

        # Handle NO_GROUP scope
        if group_scope == GroupDumpScope.NO_GROUP and self.grouped_node_uuids:
            filters.setdefault('uuid', {}).setdefault('!in', []).extend(self.grouped_node_uuids)

        # Build query
        qb = orm.QueryBuilder()
        relationships: Dict[str, Any] = {}

        # Add group filter for IN_GROUP scope
        if group_scope == GroupDumpScope.IN_GROUP and group:
            qb.append(orm.Group, filters={'uuid': group.uuid}, tag=self.GROUP_TAG)
            relationships['with_group'] = self.GROUP_TAG

        # Add entity filters (User, Computer, Code)
        if isinstance(self.config, (GroupDumpConfig, ProfileDumpConfig)):
            qb, entity_relationships = self._resolve_qb_appends(qb)
            relationships.update(entity_relationships)

            # # Add edge filter for Code links
            # if 'with_incoming' in relationships and relationships['with_incoming'] == self.CODE_TAG:
            #     relationships['edge_filters'] = {'label': 'code'}

        # Add main node type
        qb.append(orm_type, filters=filters, tag=self.NODE_TAG, **relationships)

        if self.NODE_TAG not in qb._projections:
            qb.add_projection(self.NODE_TAG, '*')

        return qb.all(flat=True)

    def _exclude_tracked_nodes(self, nodes: list[orm.ProcessNode], store_type: str) -> list[orm.ProcessNode]:
        """Exclude nodes that are already tracked in the dump tracker.

        :param nodes: Initial list of nodes
        :param store_type: Target store (calculations or workflows)
        :return: List of initial nodes with already tracked (dumped) nodes removed
        """
        if not nodes:
            return nodes

        try:
            registry = self.dump_tracker.registries[cast(RegistryNameType, store_type)]
            tracked_uuids = set(registry.entries.keys())

            if not tracked_uuids:
                return nodes

            return_nodes = []
            set_progress_bar_tqdm(bar_format=DUMP_PROGRESS_BAR_FORMAT)

            progress_desc = f"{click.style('Report', fg='blue', bold=True)}: Excluding already dumped {store_type}..."
            with get_progress_reporter()(desc=progress_desc, total=len(nodes)) as progress:
                for node in nodes:
                    if node.uuid not in tracked_uuids:
                        return_nodes.append(node)

                    progress.update()

            logger.report(f'Applied exclusion of previously dumped {store_type}.')

            return return_nodes

        except ValueError as e:
            logger.error(f"Error getting registry for '{store_type}': {e}")
            return nodes

    def _apply_behavioral_filters(self, nodes: list[orm.ProcessNode], store_type: str) -> list[orm.ProcessNode]:
        """Apply top-level and caller filters based on configuration.

        :param nodes: Initial list of nodes
        :param store_type: Target store (calculations or workflows)
        :return: Filtered list of nodes, with top-level and group membership filters applied
        """

        if not nodes:
            return nodes

        assert isinstance(self.config, (GroupDumpConfig, ProfileDumpConfig))
        # Determine if we should apply top-level filtering
        should_filter = (store_type == 'workflows' and self.config.only_top_level_workflows) or (
            store_type == 'calculations' and self.config.only_top_level_calcs
        )

        if not should_filter:
            return nodes

        # Apply caller filter (keep top-level or explicitly grouped)
        filtered_nodes = []
        set_progress_bar_tqdm(bar_format=DUMP_PROGRESS_BAR_FORMAT)

        progress_desc = f"{click.style('Report', fg='blue', bold=True)}: Applying filters to {store_type}..."
        with get_progress_reporter()(desc=progress_desc, total=len(nodes)) as progress:
            for node in nodes:
                is_sub_node = bool(getattr(node, 'caller', None))
                is_explicitly_grouped = node.uuid in self.grouped_node_uuids

                if not is_sub_node or is_explicitly_grouped:
                    filtered_nodes.append(node)

                progress.update()

        logger.report(f'Applied relevant filters to {store_type}.')

        return filtered_nodes

    def _detect_new_nodes(self, group: Optional[orm.Group] = None) -> ProcessingQueue:
        """Detect new/modified nodes for dumping.

        :param group: Specific group to detect changes for, or None for general detection
        :return: ProcessingQueue containing new/modified nodes
        """
        # Determine scope
        assert isinstance(self.config, (GroupDumpConfig, ProfileDumpConfig))
        if group is not None:
            scope = GroupDumpScope.IN_GROUP
        elif self.config.group_scope == GroupDumpScope.NO_GROUP:
            scope = GroupDumpScope.NO_GROUP
        else:
            scope = GroupDumpScope.ANY

        return self.get_nodes(group_scope=scope, group=group, apply_filters=True, exclude_tracked=True)

    def _get_ungrouped_nodes(self) -> ProcessingQueue:
        """Get all ungrouped nodes, ignoring time filters."""
        # Set `exclude_tracked` to False in the edge case that a node that was previously in a group, then the group got
        # deleted (but not the node), and the node now ends up being ungrouped, and because of `--also-ungrouped` it
        # should be dumped in the `ungrouped` directory
        # PRCOMMENT: Not sure if I should ignore time filters here. It's necessary to pick up _all_ nodes, e.g., ones
        # that end up being ungrouped after group deletion (see above), that have an `mtime` before the last dump.
        # However, that means that time filters are fully ignored. Maybe it's OK anyway in the ungrouped case.
        return self.get_nodes(
            group_scope=GroupDumpScope.NO_GROUP, apply_filters=True, ignore_time_filters=True, exclude_tracked=False
        )

    def _detect_node_changes(self, group: Optional[orm.Group] = None) -> NodeChanges:
        """Detect node changes (main orchestration method).

        :param group: The specific group to filter by when scope is IN_GROUP
        :return: Populated ``NodeChanges`` instance
        """
        new_nodes_queue = self._detect_new_nodes(group)
        deleted_node_uuids = self._detect_deleted_nodes()

        return NodeChanges(
            new_or_modified=new_nodes_queue,
            deleted=deleted_node_uuids,
        )

    def _detect_deleted_nodes(self) -> set[str]:
        """Detect nodes deleted from DB since last dump."""
        deleted_node_uuids: set[str] = set()

        for registry_name, dump_registry in self.dump_tracker.iter_by_type():
            if registry_name == 'groups':
                continue  # Skip groups registry if only processing nodes

            if not dump_registry:
                continue

            dumped_uuids = set(dump_registry.entries.keys())

            if not dumped_uuids:
                continue

            # Query existing UUIDs in DB
            qb = orm.QueryBuilder()
            orm_type = REGISTRY_TO_ORM_TYPE[registry_name]
            qb.append(orm_type, project=['uuid'])
            all_db_uuids = set(qb.all(flat=True))

            # Find missing UUIDs
            missing_uuids = dumped_uuids - all_db_uuids
            if missing_uuids:
                deleted_node_uuids.update(missing_uuids)

        return deleted_node_uuids

    def _detect_new_groups(self, current_mapping: GroupNodeMapping) -> list[GroupInfo]:
        """Identifies all groups in the current mapping as 'new' with their labels.

        :param current_mapping: Instance of ``GroupNodeMapping`` with current DB state
        :return: List of populated ``GroupInfo`` objects
        """
        new_groups = []
        for group_uuid, node_uuids in current_mapping.group_to_nodes.items():
            group = orm.load_group(group_uuid)
            group_info = GroupInfo(uuid=group_uuid, node_count=len(node_uuids), label=group.label)
            new_groups.append(group_info)
        return new_groups

    def _detect_group_changes(
        self,
        previous_mapping: GroupNodeMapping | None,
        current_mapping: GroupNodeMapping,
        specific_group_uuid: str | None = None,
    ) -> GroupChanges:
        """Detect changes between stored and current group mappings.

        :param previous_mapping: ``GroupNodeMapping`` of a previous dump (if existing)
        :param current_mapping: ``GroupNodeMapping`` of the current DB state
        :param specific_group_uuid: Restrict changes to this group, defaults to None
        :return: Populated ``GroupChanges`` object
        """

        if not previous_mapping:
            new_groups = self._detect_new_groups(current_mapping)
            group_changes = GroupChanges(new=new_groups)

        else:
            group_changes = previous_mapping.diff(current_mapping)
            self_group_uuids = set(previous_mapping.group_to_nodes.keys())
            other_group_uuids = set(current_mapping.group_to_nodes.keys())
            common_group_uuids = self_group_uuids & other_group_uuids
            # Only check for renames on groups that are actually tracked
            tracked_group_uuids = set(self.dump_tracker.registries['groups'].entries.keys())
            groups_to_check_for_rename = common_group_uuids & tracked_group_uuids

            for group_uuid in groups_to_check_for_rename:
                entry = self.dump_tracker.get_entry(group_uuid)

                old_path = entry.path
                current_group = orm.load_group(uuid=group_uuid)
                current_path_abs = self.dump_paths.get_path_for_group(group=current_group)

                if old_path.resolve() != current_path_abs.resolve():
                    msg = (
                        f'Detected rename for group UUID {group_uuid}: '
                        f"Old path '{old_path.name}', New path '{current_path_abs.name}'"
                    )
                    logger.report(msg)
                    group_changes.renamed.append(
                        GroupRenameInfo(
                            uuid=group_uuid,
                            old_path=old_path,
                            new_path=current_path_abs,
                            new_label=current_group.label,
                        )
                    )

        # Filter for specific group if requested
        # TODO: Improve this such that not all changes are first evaluated and then filtered again
        if specific_group_uuid:
            return self._filter_group_changes_for_group(group_changes, specific_group_uuid)

        return group_changes

    def _filter_group_changes_for_group(self, changes: GroupChanges, group_uuid: str) -> GroupChanges:
        """Filter GroupChangeInfo results for a specific group.

        :param changes: Populated ``GroupChanges`` instance
        :param group_uuid: UUID of group to filter for
        :return: ``GroupChanges`` instance containing only the changes for the given group
        """
        filtered_changes = GroupChanges(
            deleted=[g for g in changes.deleted if g.uuid == group_uuid],
            new=[g for g in changes.new if g.uuid == group_uuid],
            modified=[g for g in changes.modified if g.uuid == group_uuid],
            renamed=[r for r in changes.renamed if r.uuid == group_uuid],
            node_membership={},
        )

        # Filter node membership changes
        for node_uuid, membership in changes.node_membership.items():
            filtered_membership = NodeMembershipChange()
            involved = False

            if group_uuid in membership.added_to:
                filtered_membership.added_to.append(group_uuid)
                involved = True

            if group_uuid in membership.removed_from:
                filtered_membership.removed_from.append(group_uuid)
                involved = True

            if involved:
                filtered_changes.node_membership[node_uuid] = filtered_membership

        return filtered_changes

    def _resolve_time_filters(self) -> Dict[str, Any]:
        """Create time-based query filters based on dump configuration."""
        time_filters: Dict[str, Any] = {}
        assert isinstance(self.config, (GroupDumpConfig, ProfileDumpConfig))

        # Skip if no time filters requested
        if not (
            self.config.filter_by_last_dump_time
            or self.config.past_days
            or self.config.start_date
            or self.config.end_date
        ):
            return time_filters

        now = self.dump_times.current

        # Upper bound
        upper_bound = now
        if self.config.end_date is not None:
            upper_bound = min(now, self.config.end_date.astimezone())
        time_filters['<='] = upper_bound

        # Lower bound (priority: past_days > start_date > last_dump_time)
        lower_bound: Optional[datetime] = None

        if self.config.past_days is not None:
            days = int(self.config.past_days)
            lower_bound = now - timedelta(days=days)
        elif self.config.start_date is not None:
            lower_bound = self.config.start_date.astimezone()
        elif self.config.filter_by_last_dump_time and self.dump_times.last is not None:
            lower_bound = self.dump_times.last.astimezone()

        if lower_bound:
            if lower_bound > upper_bound:
                msg = (
                    f'Calculated start time {lower_bound.isoformat()} is after end time '
                    f'{upper_bound.isoformat()}. Query might yield no results.'
                )
                logger.warning(msg)
            time_filters['>='] = lower_bound

        return time_filters

    def _resolve_qb_appends(self, qb: orm.QueryBuilder) -> Tuple[orm.QueryBuilder, Dict]:
        """Appends related entity filters (User, Computer, Code) based on config.

        :param qb: QueryBuilder instance
        :return: Tuple of QueryBuilder instance with additional filters and dictionary holding the ``relationships``
        """
        relationships_to_add = {}
        assert isinstance(self.config, (GroupDumpConfig, ProfileDumpConfig))

        # User filter
        if self.config.user:
            if self.config.user.pk is not None:
                qb.append(orm.User, filters={'id': self.config.user.pk}, tag=self.USER_TAG)
                relationships_to_add['with_user'] = self.USER_TAG
            else:
                logger.warning(f'Invalid user provided: {self.config.user}. Skipping filter.')

        if self.config.codes and self.config.computers:
            msg = (
                "Cannot specify both 'codes' and 'computers' filters simultaneously. "
                'Codes are already tied to specific computers.'
            )
            raise ValueError(msg)

        # Computer filter
        if self.config.computers:
            computer_pks = [comp.pk for comp in self.config.computers if comp.pk is not None]
            if computer_pks:
                # Batch the filter to avoid database parameter limits
                filter_clauses = [
                    {'id': {'in': pk_batch}} for _, pk_batch in batch_iter(computer_pks, DEFAULT_FILTER_SIZE)
                ]
                computer_filter = {'or': filter_clauses} if len(filter_clauses) > 1 else filter_clauses[0]
                qb.append(orm.Computer, filters=computer_filter, tag=self.COMPUTER_TAG)
                relationships_to_add['with_computer'] = self.COMPUTER_TAG

        # Code filter
        elif self.config.codes:
            code_pks = [code.pk for code in self.config.codes if code.pk is not None]
            if code_pks:
                # Batch the filter to avoid database parameter limits
                filter_clauses = [{'id': {'in': pk_batch}} for _, pk_batch in batch_iter(code_pks, DEFAULT_FILTER_SIZE)]
                code_filter = {'or': filter_clauses} if len(filter_clauses) > 1 else filter_clauses[0]
                qb.append(orm.Code, filters=code_filter, tag=self.CODE_TAG)
                relationships_to_add['with_incoming'] = self.CODE_TAG
            elif self.config.codes:
                logger.warning('Code filter provided, but no valid/loaded Code objects found. Skipping.')

        return qb, relationships_to_add

    @staticmethod
    def get_calculation_descendants(workflows: list[orm.WorkflowNode]) -> list[orm.ProcessNode]:
        """Get CalculationNode descendants of the provided workflows."""
        descendants: list[orm.ProcessNode] = []
        for workflow in workflows:
            descendants.extend(node for node in workflow.called_descendants)
        return list(set(descendants))
