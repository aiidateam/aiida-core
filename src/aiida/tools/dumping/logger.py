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
from dataclasses import dataclass, field, fields
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from aiida.common import timezone
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.mapping import GroupNodeMapping
from aiida.tools.dumping.utils.helpers import DumpStoreKeys, StoreNameType
from aiida.tools.dumping.utils.paths import DumpPaths

logger = AIIDA_LOGGER.getChild('tools.dumping.logger')


@dataclass
class DumpLog:
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
    def from_dict(cls, data: dict) -> 'DumpLog':
        symlinks = []
        if data.get('symlinks'):
            symlinks = [Path(path) for path in data['symlinks']]
        # Add mtime deserialization if included
        # mtime = datetime.fromisoformat(data['mtime']) if data.get('mtime') else None
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

        dir_size = data.get('dir_size')  # Size should be stored as int

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
class DumpLogStore:
    """A store for DumpLog entries, indexed by UUID."""

    entries: Dict[str, DumpLog] = field(default_factory=dict)

    def add_entry(self, uuid: str, entry: DumpLog) -> None:
        """Add a single entry to the container."""
        self.entries[uuid] = entry

    def add_entries(self, entries: Dict[str, DumpLog]) -> None:
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

    def get_entry(self, uuid: str) -> Optional[DumpLog]:
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
    def from_dict(cls, data: Dict) -> DumpLogStore:
        store = cls()
        for uuid, entry_data in data.items():
            store.entries[uuid] = DumpLog.from_dict(entry_data)
        return store

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


@dataclass
class DumpLogStoreCollection:
    """Represents the entire log data."""

    calculations: DumpLogStore = field(default_factory=DumpLogStore)
    workflows: DumpLogStore = field(default_factory=DumpLogStore)
    groups: DumpLogStore = field(default_factory=DumpLogStore)
    data: DumpLogStore = field(default_factory=DumpLogStore)


class DumpLogger:
    """Handles loading, saving, and accessing dump log data."""

    def __init__(
        self,
        dump_paths: DumpPaths,
        stores: DumpLogStoreCollection,
        last_dump_time_str: str | None = None,
    ) -> None:
        """
        Initialize the DumpLogger. Should typically be instantiated via `load`.
        """
        self.dump_paths = dump_paths
        # Stores are now passed in directly
        self.calculations = stores.calculations
        self.workflows = stores.workflows
        self.groups = stores.groups
        self.data = stores.data
        # Store the raw string time from the log
        self._last_dump_time_str = last_dump_time_str

    @staticmethod
    def load(
        dump_paths: DumpPaths,
    ) -> Tuple[DumpLogStoreCollection, GroupNodeMapping | None, str | None]:
        """Load log data and mapping from the log file.

        Returns:
            A tuple containing:
                - DumpLogStoreCollection: The loaded stores.
                - GroupNodeMapping | None: The loaded group mapping, or None if not found/error.
                - str | None: The ISO timestamp string of the last dump, or None.

        :param dump_paths: _description_
        :return: _description_
        """
        stores = DumpLogStoreCollection()  # Default empty stores
        group_node_mapping = None
        last_dump_time_str = None

        if not dump_paths.log_path.exists():
            logger.debug(f'Log file not found at {dump_paths.log_path}, returning empty log data.')
            return stores, group_node_mapping, last_dump_time_str

        try:
            with dump_paths.log_path.open('r', encoding='utf-8') as f:
                prev_dump_data = json.load(f)

            # Load last dump time string
            last_dump_time_str = prev_dump_data.get('last_dump_time')

            # Load group-node mapping if present
            if 'group_node_mapping' in prev_dump_data:
                try:
                    group_node_mapping = GroupNodeMapping.from_dict(prev_dump_data['group_node_mapping'])
                except Exception as e:
                    logger.warning(f'Error loading group-node mapping: {e!s}')

            # Load store data using deserialize_logs helper
            stores.calculations = DumpLogger._deserialize_logs(
                prev_dump_data.get('calculations', {}), dump_paths=dump_paths
            )
            stores.workflows = DumpLogger._deserialize_logs(prev_dump_data.get('workflows', {}), dump_paths=dump_paths)
            stores.groups = DumpLogger._deserialize_logs(prev_dump_data.get('groups', {}), dump_paths=dump_paths)
            stores.data = DumpLogger._deserialize_logs(prev_dump_data.get('data', {}), dump_paths=dump_paths)

        except (json.JSONDecodeError, OSError, ValueError) as e:
            logger.warning(f'Error loading dump log file {dump_paths.log_path}: {e!s}')
            # Return default empty data on error
            return DumpLogStoreCollection(), None, None

        return stores, group_node_mapping, last_dump_time_str

    def get_last_dump_time(self) -> datetime | None:
        """Parse and return the last dump time, if available."""
        if self._last_dump_time_str:
            try:
                return datetime.fromisoformat(self._last_dump_time_str)
            except ValueError:
                logger.warning(f'Could not parse last dump time string: {self._last_dump_time_str}')
        return None

    def add_entry(self, store_key: StoreNameType, uuid: str, entry: DumpLog) -> None:
        """Add a log entry for a node to the specified store."""
        store = self.get_store_by_name(store_key)
        store.add_entry(uuid, entry)

    def del_entry(self, store_key: StoreNameType, uuid: str) -> bool:
        """Delete a log entry from the specified store."""
        store = self.get_store_by_name(store_key)
        return store.del_entry(uuid)

    @property
    def stores_collection(self) -> DumpLogStoreCollection:
        """Retrieve the current state of the log stores as a dataclass."""
        # Corrected: use the instance's stores
        return DumpLogStoreCollection(
            calculations=self.calculations,
            workflows=self.workflows,
            groups=self.groups,
            data=self.data,
        )

    # TODO: This currently requires the dump time as argument, not sure if this is what I want
    def save(
        self,
        current_dump_time: datetime,
        group_node_mapping: GroupNodeMapping | None = None,
    ) -> None:
        """Save the current log state and mapping to the JSON file."""
        log_dict = {
            # Use the _serialize_logs helper method
            'calculations': self._serialize_logs(self.calculations),
            'workflows': self._serialize_logs(self.workflows),
            'groups': self._serialize_logs(self.groups),
            'data': self._serialize_logs(self.data),
            'last_dump_time': current_dump_time.isoformat(),
        }

        if group_node_mapping:
            log_dict['group_node_mapping'] = group_node_mapping.to_dict()

        try:
            with self.dump_paths.log_path.open('w', encoding='utf-8') as f:
                json.dump(log_dict, f, indent=4)
            logger.debug(f'Dump log saved to {self.dump_paths.log_path}')
        except OSError as e:
            logger.error(f'Failed to save dump log to {self.dump_paths.log_path}: {e!s}')

    def _serialize_logs(self, container: DumpLogStore) -> Dict:
        """Serialize log entries to a dictionary format relative to dump parent."""
        serialized = {}
        for uuid, entry in container.entries.items():
            try:
                # Use the DumpLog's to_dict method which now includes new fields
                entry_dict = entry.to_dict()  # <-- This dict now contains all fields

                # Convert paths to relative strings for serialization
                # Ensure keys exist before attempting conversion
                if 'path' in entry_dict and entry_dict['path'] is not None:
                    entry_dict['path'] = str(Path(entry_dict['path']).relative_to(self.dump_paths.parent))
                if 'symlinks' in entry_dict:
                    entry_dict['symlinks'] = [
                        str(Path(p).relative_to(self.dump_paths.parent)) for p in entry_dict['symlinks']
                    ]
                if 'duplicates' in entry_dict:
                    entry_dict['duplicates'] = [
                        str(Path(p).relative_to(self.dump_paths.parent)) for p in entry_dict['duplicates']
                    ]

                # Add the complete entry dict (including mtime/size) to serialized output
                serialized[uuid] = entry_dict  # <-- Use the full dict from to_dict()

            except ValueError:
                # Fallback if path is not relative - use absolute paths from to_dict()
                msg = (
                    f'Path {entry.path} or its links/duplicates not relative to {self.dump_paths.parent}.'
                    'Storing absolute.'
                )
                logger.warning(msg)
                serialized[uuid] = entry.to_dict()  # Store absolute paths using full dict
            except Exception as e:
                logger.error(f'Error serializing log entry for {uuid}: {e}', exc_info=True)
                # Optionally add a marker for the failed entry
                serialized[uuid] = {'error': 'Serialization failed'}
        return serialized

    @staticmethod
    def _deserialize_logs(category_data: Dict, dump_paths: DumpPaths) -> DumpLogStore:
        """Deserialize log entries using DumpLog.from_dict and make paths absolute."""
        container = DumpLogStore()
        for uuid, entry_data in category_data.items():
            try:
                log_entry: Optional[DumpLog] = None
                # Handle new format (dict)
                if isinstance(entry_data, dict) and 'path' in entry_data:
                    # Use from_dict to get all fields correctly
                    log_entry = DumpLog.from_dict(entry_data)
                    # Now make paths absolute based on dump_paths.parent
                    # Note: Assumes paths in JSON are relative to dump_paths.parent
                    log_entry.path = dump_paths.parent / log_entry.path
                    log_entry.symlinks = [dump_paths.parent / p for p in log_entry.symlinks]
                    log_entry.duplicates = [dump_paths.parent / p for p in log_entry.duplicates]

                if log_entry:
                    container.add_entry(uuid, log_entry)

            except Exception as e:
                logger.warning(f'Failed to deserialize log entry for UUID {uuid}: {e}', exc_info=True)  # Add exc_info
        return container

    def get_store_by_uuid(self, uuid: str) -> DumpLogStore | None:
        """Find the store that contains the given UUID."""
        stores_coll = self.stores_collection  # Use the property
        for field_ in fields(stores_coll):
            store = getattr(stores_coll, field_.name)
            if uuid in store.entries:
                return store
        # Return None instead of raising NotExistent for easier checking
        logger.debug(f'UUID {uuid} not found in any log store.')
        return None

    def get_store_by_name(self, name: StoreNameType) -> DumpLogStore:
        """Get the store by its string literal name."""
        stores_coll = self.stores_collection  # Use the property
        if hasattr(stores_coll, name):
            return getattr(stores_coll, name)
        else:
            store_names = [field.name for field in fields(stores_coll)]
            msg = f'Wrong store key <{name}> selected. Choose one of {store_names}.'
            raise ValueError(msg)

    def get_dump_path_by_uuid(self, uuid: str) -> Optional[Path]:
        """Find the dump path for an entity with the given UUID."""
        store = self.get_store_by_uuid(uuid=uuid)
        if store and uuid in store.entries:
            return store.entries[uuid].path
        return None

    def get_store_by_orm(self, orm_type) -> DumpLogStore:
        """Get the appropriate store for a given ORM type using DumpStoreKeys."""
        store_key_str = DumpStoreKeys.from_class(orm_type)
        return self.get_store_by_name(store_key_str)  # Use existing method

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

        stores_coll = self.stores_collection
        for field_ in fields(stores_coll):
            store: DumpLogStore = getattr(stores_coll, field_.name)
            if not isinstance(store, DumpLogStore):
                continue

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
                except Exception as e:
                    logger.error(f'Unexpected error updating primary path for {uuid}: {e}', exc_info=True)

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
                    except Exception as e:
                        logger.error(f'Unexpected error updating symlink for {uuid}: {e}', exc_info=True)
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
                    except Exception as e:
                        logger.error(f'Unexpected error updating duplicate for {uuid}: {e}', exc_info=True)
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
