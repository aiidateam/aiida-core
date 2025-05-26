###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import annotations

import json
from collections.abc import Collection
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from aiida.common import timezone
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.mapping import GroupNodeMapping
from aiida.tools.dumping.utils.helpers import StoreNameType
from aiida.tools.dumping.utils.paths import DumpPaths

logger = AIIDA_LOGGER.getChild('tools.dumping.tracking')


@dataclass
class DumpRecord:
    """Represents a single dump log entry."""

    path: Path
    symlinks: List[Path] = field(default_factory=list)
    duplicates: List[Path] = field(default_factory=list)
    dir_mtime: Optional[datetime] = None
    dir_size: Optional[int] = None

    def to_dict(self) -> dict:
        # Add mtime serialization if included
        return {
            'path': str(self.path),
            'symlinks': [str(path) for path in self.symlinks] if self.symlinks else [],
            'duplicates': [str(path) for path in self.duplicates],
            'dir_mtime': self.dir_mtime.isoformat() if self.dir_mtime else None,
            'dir_size': self.dir_size,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DumpRecord':
        symlinks = []
        if data.get('symlinks'):
            symlinks = [Path(path) for path in data['symlinks']]
        duplicates = []
        if data.get('duplicates'):
            duplicates = [Path(path) for path in data['duplicates']]

        # Deserialize datetime from ISO string, handle None
        dir_mtime_str = data.get('dir_mtime')
        dir_mtime = None
        if dir_mtime_str:
            try:
                dir_mtime = datetime.fromisoformat(dir_mtime_str)
                # Ensure timezone-awareness if needed (assuming UTC if naive)
                if dir_mtime.tzinfo is None:
                    dir_mtime = timezone.make_aware(dir_mtime)  # Use AiiDA's timezone utility
            except ValueError:
                logger.warning(f'Could not parse dir_mtime string: {dir_mtime_str}')

        dir_size = data.get('dir_size')

        return cls(
            path=Path(data['path']),
            symlinks=symlinks,
            duplicates=duplicates,
            dir_mtime=dir_mtime,
            dir_size=dir_size,
        )

    def add_symlink(self, path: Path) -> None:
        """Add a symlink path to this log entry."""
        if path not in self.symlinks:
            self.symlinks.append(path)

    def remove_symlink(self, path_to_remove: Path) -> bool:
        """Remove a symlink path from this log entry, comparing resolved paths."""
        resolved_path_to_remove = path_to_remove.resolve()
        original_length = len(self.symlinks)
        # Filter out paths that resolve to the same location
        self.symlinks = [
            p
            for p in self.symlinks
            if not p.exists() or p.resolve() != resolved_path_to_remove  # Check exists() first for broken links
        ]
        return len(self.symlinks) < original_length

    def add_duplicate(self, path: Path) -> None:
        """Add a duplicate dump path to this log entry."""
        if path not in self.duplicates:
            self.duplicates.append(path)

    def remove_duplicate(self, path: Path) -> bool:
        """Remove a duplicate dump path from this log entry."""
        if path in self.duplicates:
            self.duplicates.remove(path)
            return True
        return False


@dataclass
class DumpRegistry:
    """A registry for DumpRecord entries, indexed by UUID."""

    entries: Dict[str, DumpRecord] = field(default_factory=dict)

    def add_entry(self, uuid: str, entry: DumpRecord) -> None:
        """Add a single entry to the container."""
        self.entries[uuid] = entry

    def add_entries(self, entries: Dict[str, DumpRecord]) -> None:
        """Add a collection of entries to the container."""
        self.entries.update(entries)

    def del_entry(self, uuid: str) -> bool:
        """Remove a single entry by UUID."""
        if uuid in self.entries:
            del self.entries[uuid]
            return True
        return False

    def del_entries(self, uuids: Collection[str]) -> None:
        """Remove a collection of entries by UUID."""
        for uuid in uuids:
            if uuid in self.entries:
                del self.entries[uuid]

    def get_entry(self, uuid: str) -> Optional[DumpRecord]:
        """Retrieve a single entry by UUID."""
        return self.entries.get(uuid)

    def __len__(self) -> int:
        """Return the number of entries in the container."""
        return len(self.entries)

    def __iter__(self):
        """Iterate over all entries."""
        return iter(self.entries.items())

    def to_dict(self) -> Dict:
        return {uuid: entry.to_dict() for uuid, entry in self.entries.items()}

    @classmethod
    def from_dict(cls, data: Dict) -> DumpRegistry:
        registry = cls()
        for uuid, entry_data in data.items():
            registry.entries[uuid] = DumpRecord.from_dict(entry_data)
        return registry

    def update_paths(self, old_str: str, new_str: str) -> None:
        """Update paths by replacing substrings."""
        # Keep this method as it operates solely on paths within the store
        for uuid, entry in self.entries.items():
            path_str = str(entry.path)
            if old_str in path_str:
                entry.path = Path(path_str.replace(old_str, new_str))
            # Update symlinks
            for i, symlink_path in enumerate(entry.symlinks):
                symlink_str = str(symlink_path)
                if old_str in symlink_str:
                    entry.symlinks[i] = Path(symlink_str.replace(old_str, new_str))
            # Update duplicates
            updated_duplicates = []
            for duplicate_path in entry.duplicates:
                duplicate_str = str(duplicate_path)
                if old_str in duplicate_str:
                    updated_duplicates.append(Path(duplicate_str.replace(old_str, new_str)))
                else:
                    updated_duplicates.append(duplicate_path)
            entry.duplicates = updated_duplicates


class DumpTracker:
    """Handles loading, saving, and accessing dump log data."""

    def __init__(
        self,
        dump_paths: DumpPaths,
        last_dump_time_str: str | None = None,
    ) -> None:
        """
        Initialize the DumpTracker. Should typically be instantiated via `load`.
        """
        self.dump_paths = dump_paths
        self.stores = {'calculations': DumpRegistry(), 'workflows': DumpRegistry(), 'groups': DumpRegistry()}
        # Store the raw string time from the log
        self._last_dump_time_str: Optional[str] = last_dump_time_str

    @classmethod
    def load(
        cls,
        dump_paths: DumpPaths,
    ) -> Tuple['DumpTracker', GroupNodeMapping | None]:
        """Load log data and mapping from the log file.

        Returns:
            A tuple containing:
                - DumpLogStoreCollection: The loaded stores.
                - GroupNodeMapping | None: The loaded group mapping, or None if not found/error.
                - str | None: The ISO timestamp string of the last dump, or None.

        :param dump_paths: _description_
        :return: _description_
        """
        tracker = cls(dump_paths)
        group_node_mapping = None

        if not dump_paths.tracking_log_file_path.exists():
            logger.debug(f'Log file not found at {dump_paths.tracking_log_file_path}, returning empty log data.')
            return tracker, group_node_mapping

        try:
            with dump_paths.tracking_log_file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)

            # Load last dump time string
            tracker._last_dump_time_str = data.get('last_dump_time')

            # Load group-node mapping if present
            if 'group_node_mapping' in data:
                group_node_mapping = GroupNodeMapping.from_dict(data['group_node_mapping'])

            # Load store data using deserialize_logs helper
            for store_name in tracker.stores:
                if store_name in data:
                    registry_data = data[store_name]
                    tracker.stores[store_name] = tracker._deserialize_registry(registry_data)

        except (json.JSONDecodeError, OSError, ValueError) as e:
            logger.warning(f'Error loading dump log file {dump_paths.tracking_log_file_path}: {e!s}')

        return tracker, group_node_mapping

    def get_last_dump_time(self) -> datetime | None:
        """Parse and return the last dump time, if available."""
        if self._last_dump_time_str:
            try:
                return datetime.fromisoformat(self._last_dump_time_str)
            except ValueError:
                logger.warning(f'Could not parse last dump time string: {self._last_dump_time_str}')
        return None

    def add_entry(self, store_key: StoreNameType, uuid: str, entry: DumpRecord) -> None:
        """Add a log entry for a node to the specified store."""
        store = self.get_store_by_name(store_key)
        store.add_entry(uuid, entry)

    def del_entry(self, store_key: StoreNameType, uuid: str) -> bool:
        """Delete a log entry from the specified store."""
        store = self.get_store_by_name(store_key)
        return store.del_entry(uuid)

    # TODO: This currently requires the dump time as argument, not sure if this is what I want
    def save(
        self,
        current_dump_time: datetime,
        group_node_mapping: GroupNodeMapping | None = None,
    ) -> None:
        """Save the current log state and mapping to the JSON file."""
        log_dict: dict[str, Any] = {
            store_name: self._serialize_registry(registry) for store_name, registry in self.stores.items()
        }
        log_dict['last_dump_time'] = current_dump_time.isoformat()

        if group_node_mapping:
            log_dict['group_node_mapping'] = group_node_mapping.to_dict()

        try:
            with self.dump_paths.tracking_log_file_path.open('w', encoding='utf-8') as f:
                json.dump(log_dict, f, indent=4)
            logger.debug(f'Dump log saved to {self.dump_paths.tracking_log_file_path}')
        except OSError as e:
            logger.error(f'Failed to save dump log to {self.dump_paths.tracking_log_file_path}: {e!s}')

    def _serialize_registry(self, container: DumpRegistry) -> Dict:
        """Serialize log entries to a dictionary format relative to dump parent."""
        serialized = {}
        for uuid, entry in container.entries.items():
            try:
                # Use the DumpLog's to_dict method which now includes new fields
                entry_dict = entry.to_dict()  # <-- This dict now contains all fields

                # Convert paths to relative strings for serialization
                # Ensure keys exist before attempting conversion
                if 'path' in entry_dict and entry_dict['path'] is not None:
                    entry_dict['path'] = str(Path(entry_dict['path']).relative_to(self.dump_paths.base_output_path))
                if 'symlinks' in entry_dict:
                    entry_dict['symlinks'] = [
                        str(Path(p).relative_to(self.dump_paths.base_output_path)) for p in entry_dict['symlinks']
                    ]
                if 'duplicates' in entry_dict:
                    entry_dict['duplicates'] = [
                        str(Path(p).relative_to(self.dump_paths.base_output_path)) for p in entry_dict['duplicates']
                    ]

                # Add the complete entry dict (including mtime/size) to serialized output
                serialized[uuid] = entry_dict  # <-- Use the full dict from to_dict()

            except ValueError:
                # Fallback if path is not relative - use absolute paths from to_dict()
                msg = (
                    f'Path {entry.path} or its links/duplicates not relative to {self.dump_paths.base_output_path}.'
                    'Storing absolute.'
                )
                logger.warning(msg)
                serialized[uuid] = entry.to_dict()  # Store absolute paths using full dict
        return serialized

    def _deserialize_registry(self, data: Dict) -> DumpRegistry:
        """Deserialize log entries using DumpLog.from_dict and make paths absolute."""
        container = DumpRegistry()
        for uuid, entry_data in data.items():
            log_entry: Optional[DumpRecord] = None
            # Handle new format (dict)
            if isinstance(entry_data, dict) and 'path' in entry_data:
                # Use from_dict to get all fields correctly
                log_entry = DumpRecord.from_dict(entry_data)
                # Now make paths absolute based on dump_paths.base_output_path
                # Note: Assumes paths in JSON are relative to dump_paths.base_output_path
                log_entry.path = self.dump_paths.base_output_path / log_entry.path
                log_entry.symlinks = [self.dump_paths.base_output_path / p for p in log_entry.symlinks]
                log_entry.duplicates = [self.dump_paths.base_output_path / p for p in log_entry.duplicates]

            if log_entry:
                container.add_entry(uuid, log_entry)

        return container

    def get_store_by_name(self, name: StoreNameType) -> DumpRegistry:
        """Get store by name."""
        if name not in self.stores:
            raise ValueError(f'Invalid store key: {name}. Available: {list(self.stores.keys())}')
        return self.stores[name]

    def get_store_by_uuid(self, uuid: str) -> Optional[DumpRegistry]:
        """Find store containing the UUID."""
        for store in self.stores.values():
            if uuid in store.entries:
                return store
        return None

    def get_dump_path_by_uuid(self, uuid: str) -> Optional[Path]:
        """Find the dump path for an entity with the given UUID."""
        store = self.get_store_by_uuid(uuid=uuid)
        if store and uuid in store.entries:
            return store.entries[uuid].path
        return None

    def update_paths(self, old_base_path: Path, new_base_path: Path) -> int:
        """Update all paths across all stores if they start with old_base_path.

        Replaces the old_base_path prefix with new_base_path.

        Args:
            old_base_path: The absolute base path prefix to find.
            new_base_path: The absolute base path prefix to replace with.

        Returns:
            The total number of path entries (primary path, symlinks, duplicates) updated.
        """
        update_count = 0
        logger.debug(f"Updating paths in logger: Replacing prefix '{old_base_path}' with '{new_base_path}'")

        # Ensure paths are absolute and resolved for reliable comparison
        try:
            old_resolved = old_base_path.resolve()
            new_resolved = new_base_path.resolve()
        except OSError as e:
            logger.error(f'Error resolving paths for update: {e}. Aborting path update.')
            return 0

        for store in self.stores.values():
            for uuid, entry in store.entries.items():
                updated_entry = False
                # --- Update entry.path ---
                try:
                    resolved_entry_path = entry.path.resolve()
                    if resolved_entry_path.is_relative_to(old_resolved):
                        relative_part = resolved_entry_path.relative_to(old_resolved)
                        new_path = new_resolved / relative_part
                        if entry.path != new_path:
                            logger.debug(f"Updating primary path for {uuid}: '{entry.path}' -> '{new_path}'")
                            entry.path = new_path
                            updated_entry = True
                except (OSError, ValueError):  # Handle resolve() errors or path not relative
                    logger.warning(f'Could not compare/update primary path for {uuid}: {entry.path}')

                # --- Update entry.symlinks ---
                updated_symlinks = []
                for symlink_path in entry.symlinks:
                    try:
                        resolved_symlink = symlink_path.resolve()
                        if resolved_symlink.is_relative_to(old_resolved):
                            relative_part = resolved_symlink.relative_to(old_resolved)
                            new_symlink = new_resolved / relative_part
                            updated_symlinks.append(new_symlink)
                            if symlink_path != new_symlink:
                                logger.debug(f"Updating symlink for {uuid}: '{symlink_path}' -> '{new_symlink}'")
                                updated_entry = True
                        else:
                            updated_symlinks.append(symlink_path)  # Keep unchanged
                    except (OSError, ValueError):
                        logger.warning(f'Could not compare/update symlink for {uuid}: {symlink_path}')
                        updated_symlinks.append(symlink_path)  # Keep original on error
                entry.symlinks = updated_symlinks

                # --- Update entry.duplicates ---
                # (Similar logic as for symlinks)
                updated_duplicates = []
                for duplicate_path in entry.duplicates:
                    try:
                        resolved_duplicate = duplicate_path.resolve()
                        if resolved_duplicate.is_relative_to(old_resolved):
                            relative_part = resolved_duplicate.relative_to(old_resolved)
                            new_duplicate = new_resolved / relative_part
                            updated_duplicates.append(new_duplicate)
                            if duplicate_path != new_duplicate:
                                logger.debug(
                                    f"Updating duplicate path for {uuid}: '{duplicate_path}' -> '{new_duplicate}'"
                                )
                                updated_entry = True
                        else:
                            updated_duplicates.append(duplicate_path)
                    except (OSError, ValueError):
                        logger.warning(f'Could not compare/update duplicate for {uuid}: {duplicate_path}')
                        updated_duplicates.append(duplicate_path)

                entry.duplicates = updated_duplicates

                if updated_entry:
                    update_count += 1  # Count updated entries, not individual paths

        logger.info(f'Updated paths in {update_count} log entries.')
        return update_count

    def remove_symlink_from_log_entry(self, node_uuid: str, symlink_path_to_remove: Path) -> bool:
        """Finds the log entry for a node and removes a specific symlink path from it."""
        store = self.get_store_by_uuid(node_uuid)
        if not store:
            logger.warning(f'Cannot find store for node UUID {node_uuid} to remove symlink.')
            return False
        entry = store.get_entry(node_uuid)
        if not entry:
            logger.warning(f'Cannot find log entry for node UUID {node_uuid} to remove symlink.')
            return False

        removed = entry.remove_symlink(symlink_path_to_remove)
        if removed:
            logger.debug(
                f"Removed symlink reference '{symlink_path_to_remove.name}' from log entry for node {node_uuid}."
            )
        else:
            logger.debug(
                f"Symlink reference '{symlink_path_to_remove.name}' not found in log entry for node {node_uuid}."
            )
        return removed
