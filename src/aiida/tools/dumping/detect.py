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
from aiida.common import AIIDA_LOGGER, NotExistent
from aiida.orm import QueryBuilder
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

__all__ = ('DumpChangeDetector', 'DumpQueryHandler')

logger = AIIDA_LOGGER.getChild('tools.dumping.detect')


class DumpChangeDetector:
    """Detects changes in the database since the last dump"""

    def __init__(
        self, dump_tracker: DumpTracker, dump_paths: DumpPaths, config: DumpConfig, dump_times: DumpTimes
    ) -> None:
        """Initializes the DumpChangeDetector.

        :param dump_tracker: The tracker instance holding data from the previous dump.
        :param dump_paths: Entity holding relevant timestamps for the current dump.
        :param config: The current dump configuration object.
        :param dump_times: Entity holding relevant timestamps for the current dump.
        """
        self.dump_tracker: DumpTracker = dump_tracker
        self.config: DumpConfig = config
        self.dump_times: DumpTimes = dump_times
        self.dump_paths: DumpPaths = dump_paths
        self.node_query = DumpQueryHandler(config)
        # Cache grouped node UUIDs to avoid rebuilding mapping multiple times per run
        self._grouped_node_uuids_cache: set[str] | None = None

    @cached_property
    def grouped_node_uuids(self) -> set[str]:
        """Gets the set of UUIDs for all nodes in any group.

        :return: Set of UUIDs of all nodes in any group.
        """
        logger.debug('Building grouped node UUID set...')
        mapping = GroupNodeMapping.build_from_db()
        # Union of all sets of node UUIDs from the group_to_nodes mapping
        uuids = set().union(*mapping.group_to_nodes.values())
        logger.debug(f'Cached {len(uuids)} grouped node UUIDs.')
        return uuids

    def _query_initial_candidates(
        self, scope: GroupDumpScope, group: Optional[orm.Group] = None
    ) -> dict[str, list[orm.ProcessNode]]:
        """Query broad candidate nodes using the unified DumpNodeQuery.

        :param scope: Group-scope (in given group, not in any group, any).
        :param group: Query restricted to the given group, defaults to None
        :return:
        """
        raw_nodes: dict[str, list[orm.ProcessNode]] = {
            'workflows': [],
            'calculations': [],
        }
        nodes_to_query: list[tuple[type[orm.ProcessNode], str]] = []
        nodes_to_query.extend([(orm.WorkflowNode, 'workflows'), (orm.CalculationNode, 'calculations')])

        # Resolve base time filters ONCE before looping
        base_filters = self.node_query._resolve_time_filters(
            orm.ProcessNode,  # Use base Node type for generic time filter resolving
            dump_times=self.dump_times,
            include_time_filter=self.config.filter_by_last_dump_time,
        )

        for orm_type, registry_key in nodes_to_query:
            logger.debug(f'Querying candidate nodes of type {orm_type.__name__} with scope {scope.name}...')
            nodes = self.node_query._get_nodes(
                orm_type=orm_type,
                dump_times=self.dump_times,
                scope=scope,
                group=group,
                base_filters=base_filters,
            )
            logger.debug(
                f'Query returned {len(nodes)} candidate nodes for {registry_key} (scope: {scope.name}, pre-filtering).'
            )
            raw_nodes[registry_key] = nodes
        return raw_nodes

    def _apply_logged_status_filter(
        self, raw_nodes: dict[str, list[orm.ProcessNode]]
    ) -> dict[str, list[orm.ProcessNode]]:
        """Filter out nodes that are already present in the dump tracker.

        :param raw_nodes: _description_
        :return: _description_
        """

        logger.debug('Applying logged status filter...')
        logged_filtered_nodes: dict[str, list[orm.ProcessNode]] = {
            'workflows': [],
            'calculations': [],
        }
        for registry_key, nodes in raw_nodes.items():
            if not nodes:
                continue
            try:
                # Get the appropriate log store (calculations, workflows, etc.)
                registry = self.dump_tracker.get_registry_by_name(cast(StoreNameType, registry_key))
                logged_uuids = set(registry.entries.keys())

                if not logged_uuids:  # If registry is empty, keep all nodes
                    filtered_list = nodes
                else:
                    # Keep nodes whose UUIDs are NOT in the logged set
                    filtered_list = [node for node in nodes if node.uuid not in logged_uuids]

                logged_filtered_nodes[registry_key] = filtered_list
            except ValueError as e:  # Catch potential errors from get_store_by_name
                logger.error(f"Error getting log store for key '{registry_key}': {e}")
                logged_filtered_nodes[registry_key] = nodes  # Keep original nodes on error

        return logged_filtered_nodes

    def _filter_nodes_by_caller(self, node_list: list[orm.ProcessNode]) -> list[orm.ProcessNode]:
        """Filter nodes keeping only top-level ones or those explicitly grouped.

        :param node_list: List of nodes to filter.
        :param node_type: Type of node ("workflows" or "calculations") for logging.
        :param grouped_uuids: Set of UUIDs for nodes that are explicitly grouped.
        :return: A tuple containing the filtered list of nodes and the count of removed nodes.
        :rtype: tuple[list[TNode], int]
        """
        filtered_nodes: list[orm.ProcessNode] = []

        for node in node_list:
            # Check if node has a caller (i.e., is sub-node)
            # Use getattr with default to avoid exception if 'caller' doesn't exist
            is_sub_node = bool(getattr(node, 'caller', None))
            is_explicitly_grouped = node.uuid in self.grouped_node_uuids

            # Keep if: not a sub-node OR is explicitly grouped
            if not is_sub_node or is_explicitly_grouped:
                filtered_nodes.append(node)

        return filtered_nodes

    def _apply_top_level_filter(
        self, logged_filtered_nodes: dict[str, list[orm.ProcessNode]]
    ) -> DumpNodeStore:
        """Apply the top-level calculation/workflow filter.

        If calculations or workflows are explicitly part of a group, they are kept,
        even if they are sub-calculations of a workflow.

        :param logged_filtered_nodes: Dictionary containing lists of 'workflows' and 'calculations'.
        :return: Dictionary with nodes filtered based on top-level status or grouping.
        """

        final_filtered_nodes: DumpNodeStore = DumpNodeStore()

        # --- Filter Workflows ---
        wf_list = logged_filtered_nodes.get('workflows', [])
        if self.config.only_top_level_workflows and wf_list:
            final_filtered_nodes.workflows = self._filter_nodes_by_caller(wf_list)
        else:
            final_filtered_nodes.workflows = wf_list

        # --- Filter Calculations ---
        calc_list = logged_filtered_nodes.get('calculations', [])
        if self.config.only_top_level_calcs and calc_list:
            final_filtered_nodes.calculations = self._filter_nodes_by_caller(calc_list)
        else:
            final_filtered_nodes.calculations = calc_list

        return final_filtered_nodes

    def _detect_new_nodes(self, scope: GroupDumpScope, group: Optional[orm.Group] = None) -> DumpNodeStore:
        """Detect new/modified nodes for a given scope, applying post-query filters.

        :param scope: Determines the query scope (ANY, IN_GROUP, NO_GROUP), defaults to GroupDumpScope.ANY
        :param group: The specific group to filter by when scope is IN_GROUP, defaults to None
        :return: Returns a DumpNodeStore instance that holds the selected nodes.
        """

        # Query initial candidates using the unified querier and scope
        raw_nodes = self._query_initial_candidates(scope, group)

        # Apply logged status filter
        logged_filtered_nodes = self._apply_logged_status_filter(raw_nodes)

        # Apply top-level filter (with exception for grouped calcs)
        final_filtered_nodes = self._apply_top_level_filter(logged_filtered_nodes)

        return final_filtered_nodes

    def _detect_deleted_nodes(self) -> set[str]:
        """Detect nodes deleted from DB since last dump."""
        deleted_node_uuids: set[str] = set()

        # Iterate through the ORM types we might have logged
        for orm_type in (
            orm.CalculationNode,
            orm.WorkflowNode,
        ):
            store_name = DumpStoreKeys.from_class(orm_class=orm_type)
            try:
                dump_store = self.dump_tracker.get_registry_by_name(name=store_name)
                if not dump_store:
                    # Store might not exist if no nodes of this type were ever logged
                    continue

                dumped_uuids = set(dump_store.entries.keys())
                if not dumped_uuids:
                    # Skip if no nodes of this type were logged
                    continue

                # Query for existing UUIDs of this type in the database
                qb = QueryBuilder()
                qb.append(orm_type, project=['uuid'])
                all_db_uuids_for_type = cast(Set[str], set(qb.all(flat=True)))

                # Find UUIDs that were logged but are no longer in the DB
                missing_uuids = dumped_uuids - all_db_uuids_for_type
                if missing_uuids:
                    logger.debug(f'Detected {len(missing_uuids)} deleted nodes of type {orm_type.__name__}')
                    deleted_node_uuids.update(missing_uuids)
            except ValueError as e:  # Catch potential errors from get_store_by_name
                logger.error(f"Error accessing log store for type '{orm_type.__name__}': {e}")

        logger.debug(f'Total deleted node UUIDs detected: {len(deleted_node_uuids)}')
        return deleted_node_uuids

    def _detect_new_groups(self, current_mapping: GroupNodeMapping) -> list[GroupInfo]:
        """Identifies all groups in the current mapping as 'new' with their labels."""
        logger.debug('Detecting initial set of all groups as new.')

        new_groups = []
        for group_uuid, node_uuids in current_mapping.group_to_nodes.items():
            # Load the group to get its label
            group = orm.load_group(group_uuid)
            group_label = group.label

            # Create GroupInfo with label
            group_info = GroupInfo(uuid=group_uuid, node_count=len(node_uuids), label=group_label)
            new_groups.append(group_info)

        return new_groups

    def _detect_group_changes(
        self,
        stored_mapping: GroupNodeMapping | None,
        current_mapping: GroupNodeMapping,
        specific_group_uuid: str | None = None,
    ) -> GroupChanges:
        """Detect changes between stored and current group mappings.

        :param stored_mapping: _description_
        :param current_mapping: _description_
        :param specific_group_uuid: _description_, defaults to None
        :return: _description_
        """

        group_changes: GroupChanges

        # --- Calculate initial diff based on membership ---
        if stored_mapping is None:
            # If no previous mapping, consider all current groups as new
            new_groups = self._detect_new_groups(current_mapping)
            group_changes = GroupChanges(new=new_groups)
        else:
            # Calculate the difference using the mapping's diff method
            group_changes = stored_mapping.diff(current_mapping)

        # --- Detect Renames (only if stored_mapping exists) ---
        if stored_mapping:
            self_group_uuids = set(stored_mapping.group_to_nodes.keys())
            other_group_uuids = set(current_mapping.group_to_nodes.keys())
            common_group_uuids = self_group_uuids & other_group_uuids

            for group_uuid in common_group_uuids:
                # Get old path from logger
                entry = self.dump_tracker.get_entry(group_uuid)
                if entry:
                    old_path = entry.path
                else:
                    logger.debug(f'No entry for group UUID {group_uuid} in logger.')
                    continue

                # Get current group info from DB
                current_group = orm.load_group(uuid=group_uuid)
                current_label = current_group.label

                # Calculate expected current path based on current label
                current_path_abs = self.dump_paths.get_path_for_group(
                    group=current_group,
                    parent_group_content_path=None,
                )

                # Compare old path with expected current path
                if old_path.resolve() != current_path_abs.resolve():
                    msg = (
                        f'Detected rename for group UUID {group_uuid}: '
                        f"Old path '{old_path.name}', New path '{current_path_abs.name}' "
                        f"(New label: '{current_label}')"
                    )
                    logger.info(msg)
                    group_changes.renamed.append(
                        GroupRenameInfo(
                            uuid=group_uuid,
                            old_path=old_path,
                            new_path=current_path_abs,
                            new_label=current_label,
                        )
                    )

        # If a specific group is requested, filter the results
        if specific_group_uuid:
            logger.debug(f'Filtering group changes for specific group UUID: {specific_group_uuid}')
            return self._filter_group_changes_for_group(group_changes, specific_group_uuid)
        else:
            return group_changes

    def _detect_all_changes(self, group: Optional[orm.Group] = None) -> tuple[NodeChanges, GroupNodeMapping]:
        """Detect all node and group changes relevant for a dump operation.

        Orchestrates calls to more specific detection methods.

        :param group: _description_, defaults to None
        :return: _description_
        """
        logger.info('Starting change detection...')
        # Clear grouped UUID cache at the start of each full detection run
        self._grouped_node_uuids_cache = None

        # --- Get Current Mapping ---
        current_group_mapping = GroupNodeMapping.build_from_db()
        logger.debug('Successfully built current group-node mapping from DB.')

        # --- Determine Scope for Node Detection (Assign Enum member) ---
        node_detection_scope: GroupDumpScope
        if group is not None:
            node_detection_scope = GroupDumpScope.IN_GROUP
            logger.debug(f"Node detection scope set to '{node_detection_scope.name}' for group {group.label}")
        elif self.config.group_scope == GroupDumpScope.NO_GROUP:
            node_detection_scope = GroupDumpScope.NO_GROUP
            logger.debug(f"Node detection scope set to '{node_detection_scope.name}'")
        else:
            node_detection_scope = GroupDumpScope.ANY
            logger.debug(f"Node detection scope set to '{node_detection_scope.name}'")

        # --- Detect Node Changes ---
        # Call detect_new_nodes with the determined scope Enum member
        new_nodes_store: DumpNodeStore = self._detect_new_nodes(
            scope=node_detection_scope,
            group=group,  # Pass the specific group if scope is IN_GROUP
        )

        deleted_node_uuids: set[str] = self._detect_deleted_nodes()

        node_changes = NodeChanges(
            new_or_modified=new_nodes_store,
            deleted=deleted_node_uuids,
        )

        return node_changes, current_group_mapping

    def _filter_group_changes_for_group(self, changes: GroupChanges, group_uuid: str) -> GroupChanges:
        """Filter GroupChangeInfo results for a specific group.

        :param changes: _description_
        :param group_uuid: _description_
        :return: _description_
        """
        logger.debug(f'Filtering GroupChangeInfo for group UUID: {group_uuid}')
        # Create a new GroupChanges object to hold the filtered results
        filtered_changes = GroupChanges(
            deleted=[g for g in changes.deleted if g.uuid == group_uuid],
            new=[g for g in changes.new if g.uuid == group_uuid],
            modified=[g for g in changes.modified if g.uuid == group_uuid],
            node_membership={},  # Initialize as empty dict
        )

        # Filter node membership changes
        for node_uuid, membership in changes.node_membership.items():
            involved_in_this_group = False
            # Create a new NodeMembershipChange for the filtered result
            filtered_membership = NodeMembershipChange()

            # Check if the specific group is in the added list for this node
            if group_uuid in membership.added_to:
                filtered_membership.added_to.append(group_uuid)
                involved_in_this_group = True

            # Check if the specific group is in the removed list for this node
            if group_uuid in membership.removed_from:
                filtered_membership.removed_from.append(group_uuid)
                involved_in_this_group = True

            # If the node's membership changed with respect to this specific group, add it
            if involved_in_this_group:
                filtered_changes.node_membership[node_uuid] = filtered_membership

        filtered_renamed = [r for r in changes.renamed if r.uuid == group_uuid]
        filtered_changes.renamed = filtered_renamed

        logger.debug(f'Filtered group changes: {filtered_changes}')
        return filtered_changes

    @staticmethod
    def _get_calculation_descendants(
        workflows: list[orm.WorkflowNode],
    ) -> list[orm.CalculationNode]:
        """Get CalculationNode descendants of the provided workflows.

        :param workflows: _description_
        :return: _description_
        """
        descendants: list[orm.CalculationNode] = []
        for workflow in workflows:
            # Use the `called_descendants` property which handles the traversal
            descendants.extend(node for node in workflow.called_descendants if isinstance(node, orm.CalculationNode))
        # Ensure uniqueness using UUIDs as keys in a dict
        unique_descendants = list(set(descendants))
        logger.debug(f'Found {len(unique_descendants)} unique calculation descendants for {len(workflows)} workflows.')
        return unique_descendants


class DumpQueryHandler:
    """Builds and executes database queries to find nodes for dumping."""

    # Tags used in QueryBuilder for consistency
    NODE_TAG = 'node'
    GROUP_TAG = 'group_filter'
    USER_TAG = 'user_filter'
    COMPUTER_TAG = 'computer_filter'
    CODE_TAG = 'code_filter'

    def __init__(self, config: DumpConfig):
        self.config = config

    def _get_nodes(
        self,
        orm_type: Type[orm.ProcessNode],
        dump_times: DumpTimes,
        scope: GroupDumpScope = GroupDumpScope.ANY,
        group: Optional[orm.Group] = None,
        base_filters: Optional[Dict] = None,
        ignore_time_filter: bool = False,
    ) -> List[orm.ProcessNode]:
        """Query nodes based on the specified type, time, scope, and filters.

        :param orm_type: The AiiDA ORM Node class to query (e.g., CalculationNode).
        :param dump_times: Object containing relevant timestamps for filtering.
        :param scope: Determines the query scope (ANY, IN_GROUP, NO_GROUP), defaults to GroupDumpScope.ANY
        :param group: The specific group to filter by when scope is IN_GROUP, defaults to None
        :param base_filters: Pre-resolved base filters (e.g., time).
            If None, they will be resolved based on dump_times and config, defaults to None
        :raises ValueError: If scope is IN_GROUP but no group is provided.
        :return: A list of matching Node instances.
        """
        logger.debug(f"Getting nodes for type {orm_type.__name__} with scope '{scope.name}'...")

        # 1. Resolve base filters (time, etc.) if not provided
        if base_filters is None:
            include_time_filter = self.config.filter_by_last_dump_time
            resolved_filters = self._resolve_time_filters(
                orm_type=orm_type,
                dump_times=dump_times,
                include_time_filter=include_time_filter,
                ignore_time_filter=ignore_time_filter,
            )
        else:
            resolved_filters = base_filters.copy()

        # 2. Modify filters based on scope
        if scope == GroupDumpScope.IN_GROUP:
            if group is None:
                raise ValueError('Scope is IN_GROUP but no group object was provided.')
            # Group filtering handled by relationships
        elif scope == GroupDumpScope.NO_GROUP:
            grouped_node_uuids = self._query_grouped_node_uuids(orm_type)
            if grouped_node_uuids:
                if 'uuid' not in resolved_filters:
                    resolved_filters['uuid'] = {}
                resolved_filters['uuid']['!in'] = list(grouped_node_uuids)
                logger.debug(f'Query: Adding filter to exclude {len(grouped_node_uuids)} grouped nodes.')
        elif scope == GroupDumpScope.ANY:
            pass

        qb = orm.QueryBuilder()
        relationships: Dict[str, Any] = {}

        # Append Group filter if scope is IN_GROUP
        if scope == GroupDumpScope.IN_GROUP and group:
            qb.append(orm.Group, filters={'uuid': group.uuid}, tag=self.GROUP_TAG)
            relationships['with_group'] = self.GROUP_TAG

        # Append related entity filters (User, Computer, Code)
        qb, entity_relationships = self._resolve_qb_appends(qb)
        relationships.update(entity_relationships)

        # Add edge filter specifically for Code links if Code was appended
        if 'with_incoming' in relationships and relationships['with_incoming'] == self.CODE_TAG:
            relationships['edge_filters'] = {'label': 'code'}

        # Append the main node type with combined filters and relationships
        qb.append(orm_type, filters=resolved_filters, tag=self.NODE_TAG, **relationships)

        # 6. Execute query using shared helper
        if self.NODE_TAG not in qb._projections:
            qb.add_projection(self.NODE_TAG, '*')

        results: list[orm.ProcessNode] = cast(list[orm.ProcessNode], qb.all(flat=True))

        return results

    def _query_grouped_node_uuids(self, orm_type: Type[orm.ProcessNode]) -> Set[str]:
        """Helper to query UUIDs of nodes of orm_type present in any group.

        :param orm_type: _description_
        :return: _description_
        """
        logger.debug(f'Querying grouped node UUIDs for {orm_type.__name__}...')
        qb_in_group = orm.QueryBuilder()
        qb_in_group.append(orm.Group, tag='g_sub')
        qb_in_group.append(orm_type, with_group='g_sub', project='uuid', tag='n_in_g')
        grouped_uuids = set(qb_in_group.all(flat=True))
        logger.debug(f'Found {len(grouped_uuids)} grouped nodes of type {orm_type.__name__}.')
        return cast(Set[str], grouped_uuids)

    def _resolve_time_filters(
        self,
        orm_type: Type[orm.ProcessNode],
        dump_times: DumpTimes,
        include_time_filter: bool = True,
        ignore_time_filter: bool = False,
    ) -> Dict:
        """Create time-based query filters based on dump configuration.

        :param orm_type: _description_
        :param dump_times: _description_
        :param include_time_filter: _description_, defaults to True
        :return: _description_
        """
        filters: dict = {}

        # --- Time Filters ---
        # Skip adding mtime filter if ignore_time_filter is True or no time filter is explicitly requested
        if not include_time_filter or ignore_time_filter:
            logger.debug(f'Skipping time filters for {orm_type.__name__}.')
            return filters

        time_filters = {}
        # TODO: Use current dump time instead of now
        now = dump_times.current

        # --- Determine Upper Bound (end_date or now) ---
        upper_bound = now
        if self.config.end_date is not None:
            # Pydantic should have validated/parsed already
            upper_bound = min(now, self.config.end_date.astimezone())
            logger.debug(f'Using explicit end_date: {upper_bound.isoformat()}')
        time_filters['<='] = upper_bound

        # --- Determine Lower Bound (past_days, start_date, last_dump_time) ---
        lower_bound: Optional[datetime] = None

        # 1. Priority: past_days
        if self.config.past_days is not None:
            try:
                days = int(self.config.past_days)
                lower_bound = now - timedelta(days=days)
                logger.debug(f'Using past_days={days}, calculated start date: {lower_bound.isoformat()}')
            except (ValueError, TypeError):
                logger.warning(f"Invalid value for past_days: '{self.config.past_days}'. Ignoring.")

        # 2. Next Priority: start_date (only if past_days wasn't used)
        elif self.config.start_date is not None:
            # Pydantic should have validated/parsed already
            lower_bound = self.config.start_date.astimezone()
            logger.debug(f'Using explicit start_date: {lower_bound.isoformat()}')

        # 3. Fallback: filter_by_last_dump_time (only if others weren't used)
        elif self.config.filter_by_last_dump_time and dump_times.last is not None:
            lower_bound = dump_times.last.astimezone()
            logger.debug(f'Using last dump time as start date: {lower_bound.isoformat()}')

        if lower_bound:
            # Ensure lower bound is not after upper bound
            if lower_bound > upper_bound:
                msg = (
                    f'Calculated start time {lower_bound.isoformat()} is after end time '
                    '{upper_bound.isoformat()}. Query might yield no results.'
                )
                logger.warning(msg)
                # Adjust lower_bound to upper_bound to avoid invalid range? Or let QB handle it? Let QB handle.
            time_filters['>='] = lower_bound

        if time_filters:
            filters['mtime'] = time_filters
            logger.debug(f'Applying time filters for {orm_type.__name__}: {time_filters}')
        else:
            logger.debug(f'No time filters applied for {orm_type.__name__}.')

        return filters

    def _resolve_qb_appends(self, qb: QueryBuilder) -> Tuple[QueryBuilder, Dict]:
        """Appends related entity filters (User, Computer, Code) based on config.

        :param qb: _description_
        :param orm_type: _description_
        :return: _description_
        """
        relationships_to_add = {}

        # Use tags defined in the class
        user_tag = self.USER_TAG
        computer_tag = self.COMPUTER_TAG
        code_tag = self.CODE_TAG

        # --- User Filter ---
        if self.config.user:
            # Ensure user is loaded correctly before accessing pk
            if isinstance(self.config.user, orm.User) and self.config.user.pk is not None:
                qb.append(orm.User, filters={'id': self.config.user.pk}, tag=user_tag)
                relationships_to_add['with_user'] = user_tag
                logger.debug(f'QB: Appending User filter for {self.config.user.email}')
            else:
                logger.warning(f'Invalid or unloaded user provided: {self.config.user}. Skipping filter.')

        # --- Computer Filter ---
        if self.config.computers:
            computer_pks = [
                comp.pk for comp in self.config.computers if isinstance(comp, orm.Computer) and comp.pk is not None
            ]
            if computer_pks:
                qb.append(
                    orm.Computer,
                    filters={'id': {'in': computer_pks}},
                    tag=computer_tag,
                )
                # Check if relationship is 'with_computer' or something else based on orm_type
                relationships_to_add['with_computer'] = computer_tag
                # Add other relationships if needed for different node types
                logger.debug(f'QB: Appending Computer filter for PKs: {computer_pks}')
            # Check if list was provided but contained invalid items
            elif self.config.computers:
                logger.warning('Computer filter provided, but no valid/loaded Computer objects found. Skipping.')

        # --- Code Filter ---
        if self.config.codes:
            code_pks = [code.pk for code in self.config.codes if isinstance(code, orm.Code) and code.pk is not None]
            if code_pks:
                qb.append(orm.Code, filters={'id': {'in': code_pks}}, tag=code_tag)
                # NOTE: Not sure if this is needed
                relationships_to_add['with_incoming'] = code_tag
                logger.debug(f'QB: Appending Code filter for PKs: {code_pks}')
            # Check if list was provided but contained invalid items
            elif self.config.codes:
                logger.warning('Code filter provided, but no valid/loaded Code objects found. Skipping.')

        return qb, relationships_to_add

