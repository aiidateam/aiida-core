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
from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple, Type, cast

from aiida import orm
from aiida.common import AIIDA_LOGGER
from aiida.tools.dumping.config import GroupDumpScope
from aiida.tools.dumping.mapping import GroupNodeMapping
from aiida.tools.dumping.utils import (
    DumpNodeStore,
    DumpPaths,
    DumpStoreKeys,
    DumpTimes,
    GroupChanges,
    GroupInfo,
    GroupRenameInfo,
    NodeChanges,
    NodeMembershipChange,
    StoreNameType,
)

if TYPE_CHECKING:
    from aiida.tools.dumping.config import DumpConfig
    from aiida.tools.dumping.tracking import DumpTracker

__all__ = ('DumpChangeDetector',)

logger = AIIDA_LOGGER.getChild('tools.dumping.detect')


class DumpChangeDetector:
    """Detects changes in the database since the last dump."""

    NODE_TAG = 'node'
    GROUP_TAG = 'group_filter'
    USER_TAG = 'user_filter'
    COMPUTER_TAG = 'computer_filter'
    CODE_TAG = 'code_filter'

    def __init__(
        self, config: DumpConfig, dump_tracker: DumpTracker, dump_paths: DumpPaths, dump_times: DumpTimes
    ) -> None:
        """Initializes the DumpChangeDetector."""
        self.config: DumpConfig = config
        self.dump_tracker: DumpTracker = dump_tracker
        self.dump_paths: DumpPaths = dump_paths
        self.dump_times: DumpTimes = dump_times

    @cached_property
    def grouped_node_uuids(self) -> set[str]:
        """Cached property holding the set of UUIDs for all nodes in any group."""
        mapping = GroupNodeMapping.build_from_db()
        uuids = set().union(*mapping.group_to_nodes.values())
        return uuids

    def get_nodes(
        self,
        group_scope: GroupDumpScope = GroupDumpScope.ANY,
        group: Optional[orm.Group] = None,
        apply_filters: bool = True,
        ignore_time_filters: bool = False,
        exclude_tracked: bool = True,
    ) -> DumpNodeStore:
        """Unified method to get nodes with various filtering options.

        :param group_scope: Determines the query scope (ANY, IN_GROUP, NO_GROUP)
        :param group: The specific group to filter by when scope is IN_GROUP
        :param apply_filters: Whether to apply top-level and caller filters
        :param ignore_time_filters: Whether to ignore time-based filters
        :param exclude_tracked: Whether to exclude nodes already in dump tracker
        :return: DumpNodeStore containing the filtered nodes
        """
        if group_scope == GroupDumpScope.IN_GROUP and not group:
            msg = 'Scope is IN_GROUP but no group object was provided.'
            raise ValueError(msg)

        # Build base filters
        base_filters = {}
        if not ignore_time_filters:
            base_filters['mtime'] = self._resolve_time_filters()

        # Get nodes by type
        node_store = DumpNodeStore()

        for orm_type, store_attr in [(orm.WorkflowNode, 'workflows'), (orm.CalculationNode, 'calculations')]:
            nodes = self._query_single_type(
                orm_type=orm_type, group_scope=group_scope, group=group, base_filters=base_filters
            )

            # Apply exclusion filters
            if exclude_tracked:
                nodes = self._exclude_tracked_nodes(nodes, store_attr)

            # Apply behavioral filters
            if apply_filters:
                nodes = self._apply_behavioral_filters(nodes, store_attr)

            setattr(node_store, store_attr, nodes)

        return node_store

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
        :return: List of ``orm.ProcessNode``s obtained via the DB query
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
        qb, entity_relationships = self._resolve_qb_appends(qb)
        relationships.update(entity_relationships)

        # Add edge filter for Code links
        if 'with_incoming' in relationships and relationships['with_incoming'] == self.CODE_TAG:
            relationships['edge_filters'] = {'label': 'code'}

        # Add main node type
        qb.append(orm_type, filters=filters, tag=self.NODE_TAG, **relationships)

        if self.NODE_TAG not in qb._projections:
            qb.add_projection(self.NODE_TAG, '*')

        return cast(list[orm.ProcessNode], qb.all(flat=True))

    def _exclude_tracked_nodes(self, nodes: list[orm.ProcessNode], store_type: str) -> list[orm.ProcessNode]:
        """Exclude nodes that are already tracked in the dump tracker.

        :param nodes: Initial list of nodes
        :param store_type: Target store (calculations or workflows)
        :return: List of initial nodes with already tracked (dumped) nodes removed
        """
        if not nodes:
            return nodes

        try:
            registry = self.dump_tracker.get_registry_by_name(cast(StoreNameType, store_type))
            tracked_uuids = set(registry.entries.keys())

            if not tracked_uuids:
                return nodes

            return [node for node in nodes if node.uuid not in tracked_uuids]

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

        # Determine if we should apply top-level filtering
        should_filter = (store_type == 'workflows' and self.config.only_top_level_workflows) or (
            store_type == 'calculations' and self.config.only_top_level_calcs
        )

        if not should_filter:
            return nodes

        # Apply caller filter (keep top-level or explicitly grouped)
        filtered_nodes = []
        for node in nodes:
            is_sub_node = bool(getattr(node, 'caller', None))
            is_explicitly_grouped = node.uuid in self.grouped_node_uuids

            if not is_sub_node or is_explicitly_grouped:
                filtered_nodes.append(node)

        return filtered_nodes

    def _detect_new_nodes(self, group: Optional[orm.Group] = None) -> DumpNodeStore:
        """Detect new/modified nodes for dumping.

        :param group: Specific group to detect changes for, or None for general detection
        :return: DumpNodeStore containing new/modified nodes
        """
        # Determine scope
        if group is not None:
            scope = GroupDumpScope.IN_GROUP
        elif self.config.group_scope == GroupDumpScope.NO_GROUP:
            scope = GroupDumpScope.NO_GROUP
        else:
            scope = GroupDumpScope.ANY

        return self.get_nodes(group_scope=scope, group=group, apply_filters=True, exclude_tracked=True)

    def get_ungrouped_nodes(self) -> DumpNodeStore:
        """Get all ungrouped nodes, ignoring time filters."""
        return self.get_nodes(
            group_scope=GroupDumpScope.NO_GROUP, apply_filters=True, ignore_time_filters=True, exclude_tracked=True
        )

    def _detect_node_changes(self, group: Optional[orm.Group] = None) -> NodeChanges:
        """Detect node changes (main orchestration method).

        :param group: The specific group to filter by when scope is IN_GROUP
        :return: Populated ``NodeChanges`` instance
        """
        new_nodes_store = self._detect_new_nodes(group)
        deleted_node_uuids = self._detect_deleted_nodes()

        return NodeChanges(
            new_or_modified=new_nodes_store,
            deleted=deleted_node_uuids,
        )

    def _detect_deleted_nodes(self) -> set[str]:
        """Detect nodes deleted from DB since last dump."""
        deleted_node_uuids: set[str] = set()

        for orm_type in (orm.CalculationNode, orm.WorkflowNode):
            registry_name = DumpStoreKeys.from_class(orm_class=orm_type)
            dump_registry = self.dump_tracker.get_registry_by_name(name=registry_name)
            if not dump_registry:
                continue

            dumped_uuids = set(dump_registry.entries.keys())
            if not dumped_uuids:
                continue

            # Query existing UUIDs in DB
            qb = orm.QueryBuilder()
            qb.append(orm_type, project=['uuid'])
            all_db_uuids = cast(Set[str], set(qb.all(flat=True)))

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
        stored_mapping: GroupNodeMapping | None,
        current_mapping: GroupNodeMapping,
        specific_group_uuid: str | None = None,
    ) -> GroupChanges:
        """Detect changes between stored and current group mappings.

        :param stored_mapping: ``GroupNodeMapping`` of a previous dump (if existing)
        :param current_mapping: ``GroupNodeMapping`` of the current DB state
        :param specific_group_uuid: Restrict changes to this group, defaults to None
        :return: Populated ``GroupChanges`` object
        """
        # Calculate initial diff based on membership
        if stored_mapping is None:
            new_groups = self._detect_new_groups(current_mapping)
            group_changes = GroupChanges(new=new_groups)
        else:
            group_changes = stored_mapping.diff(current_mapping)

        # Detect renames (only if stored_mapping exists)
        if stored_mapping:
            self_group_uuids = set(stored_mapping.group_to_nodes.keys())
            other_group_uuids = set(current_mapping.group_to_nodes.keys())
            common_group_uuids = self_group_uuids & other_group_uuids

            for group_uuid in common_group_uuids:
                entry = self.dump_tracker.get_entry(group_uuid)
                if not entry:
                    continue

                old_path = entry.path
                current_group = orm.load_group(uuid=group_uuid)
                current_path_abs = self.dump_paths.get_path_for_group(
                    group=current_group,
                    parent_group_content_path=None,
                )

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
        # TODO: Improve this such that not all changes are evaluated and then filtered
        # But from the beginning only the changes for one group are obtained
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

    def _resolve_time_filters(self) -> Dict:
        """Create time-based query filters based on dump configuration."""
        time_filters = {}

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

        # User filter
        if self.config.user:
            if isinstance(self.config.user, orm.User) and self.config.user.pk is not None:
                qb.append(orm.User, filters={'id': self.config.user.pk}, tag=self.USER_TAG)
                relationships_to_add['with_user'] = self.USER_TAG
            else:
                logger.warning(f'Invalid user provided: {self.config.user}. Skipping filter.')

        # Computer filter
        if self.config.computers:
            computer_pks = [
                comp.pk for comp in self.config.computers if isinstance(comp, orm.Computer) and comp.pk is not None
            ]
            if computer_pks:
                qb.append(orm.Computer, filters={'id': {'in': computer_pks}}, tag=self.COMPUTER_TAG)
                relationships_to_add['with_computer'] = self.COMPUTER_TAG

        # Code filter
        if self.config.codes:
            code_pks = [code.pk for code in self.config.codes if isinstance(code, orm.Code) and code.pk is not None]
            if code_pks:
                qb.append(orm.Code, filters={'id': {'in': code_pks}}, tag=self.CODE_TAG)
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
