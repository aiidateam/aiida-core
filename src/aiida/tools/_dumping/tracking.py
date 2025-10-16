###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Infrastructure to keep a log/tracking of the progress during and between dumping operations."""

from __future__ import annotations

import json
from collections.abc import Collection
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Literal, Optional

from aiida.common import AIIDA_LOGGER, timezone
from aiida.tools._dumping.mapping import GroupNodeMapping
from aiida.tools._dumping.utils import DumpPaths, DumpTimes

logger = AIIDA_LOGGER.getChild('tools._dumping.tracking')


@dataclass
class DumpRecord:
    """Represents a single dump log entry."""

    path: Path
    symlinks: List[Path] = field(default_factory=list)
    duplicates: List[Path] = field(default_factory=list)
    dir_mtime: Optional[datetime] = None
    dir_size: Optional[int] = None

    def to_dict(self) -> dict:
        """Returns a serialized dictionary representation of the entry."""
        return {
            'path': str(self.path),
            'symlinks': [str(path) for path in self.symlinks] if self.symlinks else [],
            'duplicates': [str(path) for path in self.duplicates] if self.duplicates else [],
            'dir_mtime': self.dir_mtime.isoformat() if self.dir_mtime else None,
            'dir_size': self.dir_size if self.dir_size else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DumpRecord':
        """Returns a populated ``DumpRecord`` entry from a serialized dictionary representation.

        :param data: Dictionary with ``DumpRecord`` content (usually obtained from the log JSON file)
        :return: ``DumpRecord`` instance
        """
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
        """Add a symlink path to this ``DumpRecord`` entry.

        :param path: The path of the symlink
        """
        if path not in self.symlinks:
            self.symlinks.append(path)

    def remove_symlink(self, path: Path) -> None:
        """Remove a symlink path from this ``DumpRecord`` entry, comparing resolved paths.

        :param path: The symlink to be removed
        """
        resolved_path_to_remove = path.resolve()
        # Filter out paths that resolve to the same location
        self.symlinks = [
            p
            for p in self.symlinks
            if not p.exists() or p.resolve() != resolved_path_to_remove  # Check exists() first for broken links
        ]

    def add_duplicate(self, path: Path) -> None:
        """Add a duplicate dump path to this ``DumpRecord`` entry.

        :param path: The duplicated dump path for an AiiDa object to be added
        """
        if path not in self.duplicates:
            self.duplicates.append(path)

    def remove_duplicate(self, path: Path) -> None:
        """Remove a duplicate dump path from this ``DumpRecord`` entry.

        :param path: The duplicated dump path to be removed from the ``DumpRecord`` entry
        """
        if path in self.duplicates:
            self.duplicates.remove(path)

    def update_stats(self, path: Optional[Path]) -> None:
        """Update directory stats from the path of the ``DumpRecord`` or an optional given path.

        :param path: An optional path. If not given, the path of the ``DumpRecord`` instance is used
        """
        if not path:
            path = self.path

        self.dir_mtime, self.dir_size = DumpPaths.get_directory_stats(path)


@dataclass
class DumpRegistry:
    """A registry for ``DumpRecord`` entries, indexed by UUID."""

    entries: Dict[str, DumpRecord] = field(default_factory=dict)

    def add_entry(self, uuid: str, entry: DumpRecord) -> None:
        """Add a single ``DumpRecord`` entry to the registry.

        :param uuid: The UUID of the AiiDA node
        :param entry: The ``DumpRecord`` entry to be added
        :raises ValueError: If the UUID already exists in the registry
        """
        if uuid in self.entries:
            raise ValueError(f"UUID '{uuid}' already exists in the registry")
        self.entries[uuid] = entry

    def add_entries(self, entries: Dict[str, DumpRecord]) -> None:
        """Add a collection of ``DumpRecord`` entries to the container.

        :param entries: Dictionary of ``DumpRecord`` entries indexed by the AiiDA node UUIDs
        """
        for uuid, entry in entries.items():
            self.add_entry(uuid, entry)

    def del_entry(self, uuid: str) -> None:
        """Remove a single ``DumpRecord`` entry by its AiiDA node UUID.

        :param uuid: The UUID of the AiiDA node for which the entry should be removed
        :raises ValueError: If the UUID doesn't exist in the registry
        """
        if uuid not in self.entries:
            raise ValueError(f"UUID '{uuid}' not in the registry")
        del self.entries[uuid]

    def del_entries(self, uuids: Collection[str]) -> None:
        """Remove a collection of entries via their UUIDs.

        :param uuids: List of UUIDs whose entries should be removed from the registry
        """
        for uuid in uuids:
            self.del_entry(uuid)

    def get_entry(self, uuid: str) -> DumpRecord:
        """Retrieve a single entry via its UUID.

        :param uuid: The corresponding UUID of the entry to be retrieved
        :return: The retrieved ``DumpRecord`` entry from the registry
        :raises ValueError: If the UUID doesn't exist in the registry
        """
        if uuid not in self.entries:
            raise ValueError(f"UUID '{uuid}' not found in the registry")
        return self.entries[uuid]

    def to_dict(self) -> Dict:
        """Get a serialized dictionary representation of the ``DumpRegistry``

        :return: Serialized dictionary representation of the ``DumpRegistry``
        """
        return {uuid: entry.to_dict() for uuid, entry in self.entries.items()}

    @classmethod
    def from_dict(cls, data: Dict) -> DumpRegistry:
        """Obtain a ``DumpRegistry`` instance from a serialized dictionary representation

        :param data: Serialized dictionary representation of ``DumpRegistry`` contents
        :return: Populated ``DumpRegistry`` instance
        """
        registry = cls()
        for uuid, entry_data in data.items():
            registry.entries[uuid] = DumpRecord.from_dict(entry_data)
        return registry

    def __len__(self) -> int:
        """Return the number of entries in the container."""
        return len(self.entries)

    def __iter__(self):
        """Iterate over all entries."""
        return iter(self.entries.items())


class DumpTracker:
    """Handles loading, saving, modifying, and accessing dump log/tracking data."""

    def __init__(
        self,
        dump_paths: DumpPaths,
        dump_times: Optional[DumpTimes] = None,
        previous_mapping: Optional[GroupNodeMapping] = None,
        current_mapping: Optional[GroupNodeMapping] = None,
    ) -> None:
        """Initialize the DumpTracker. Typically be instantiated via `load`.

        :param dump_paths: Instance of ``DumpPaths``
        :param dump_times: Instance of ``DumpTimes``
        :param previous_mapping: A ``GroupNodeMapping`` of a previous dump, if existing, defaults to None
        :param current_mapping: The current ``GroupNodeMapping`` obtained from AiiDA's DB state, defaults to None
        """
        self.dump_paths: DumpPaths = dump_paths
        self.registries: Dict[str, DumpRegistry] = {
            'calculations': DumpRegistry(),
            'workflows': DumpRegistry(),
            'groups': DumpRegistry(),
        }
        self.dump_times: DumpTimes = dump_times or DumpTimes()
        self.previous_mapping: GroupNodeMapping = previous_mapping or GroupNodeMapping()
        self.current_mapping: GroupNodeMapping = current_mapping or GroupNodeMapping()

    @classmethod
    def load(cls, dump_paths: DumpPaths) -> DumpTracker:
        """Load log data from the log file to instantiate the DumpTracker.

        :param dump_paths: Path to the JSON log file to be read in
        :return: Loaded ``DumpTracker`` instance
        """
        data = {}

        # Load data from file if it exists
        if dump_paths.tracking_log_file_path.exists():
            try:
                data = json.loads(dump_paths.tracking_log_file_path.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, OSError, ValueError) as e:
                logger.warning(f'Error loading dump log file {dump_paths.tracking_log_file_path}: {e!s}')
                raise

        # Create DumpTimes and tracker instances
        dump_times = DumpTimes.from_last_log_time(data.get('last_dump_time'))

        # Load previous group-node-mapping if present
        previous_mapping = None
        if 'group_node_mapping' in data:
            previous_mapping = GroupNodeMapping.from_dict(data['group_node_mapping'])

        # `current_mapping` is set elsewhere
        tracker = cls(dump_paths, dump_times, previous_mapping=previous_mapping)

        # Load registry data
        for registry_name in tracker.registries:
            if registry_name in data:
                tracker.registries[registry_name] = tracker._deserialize_registry(data[registry_name])

        return tracker

    def save(self) -> None:
        """Save the current log state and mapping to the JSON file."""
        log_dict: dict[str, Any] = {
            registry_name: self._serialize_registry(registry) for registry_name, registry in self.registries.items()
        }
        log_dict['last_dump_time'] = self.dump_times.current.isoformat()
        log_dict['group_node_mapping'] = self.current_mapping.to_dict()

        try:
            self.dump_paths.tracking_log_file_path.write_text(json.dumps(log_dict, indent=4), encoding='utf-8')
        except OSError as e:
            logger.error(f'Failed to save dump log to {self.dump_paths.tracking_log_file_path}: {e!s}')

    def get_entry(self, uuid: str) -> DumpRecord:
        """Find the dump record for an AiiDA node with the given UUID.

        :param uuid: UUID of the AiiDA node
        :return: The dump record for the given UUID
        :raises ValueError: If the UUID is not found in any registry
        """
        registry = self._get_registry_from_entry(uuid=uuid)
        return registry.get_entry(uuid)

    def del_entry(self, uuid: str) -> None:
        """Delete a log entry by UUID (automatically finds the correct registry).

        :param uuid: The corresponding UUID of the AiiDA node for which the entry should be deleted
        :raises ValueError: If the UUID is not found in any registry
        """
        registry = self._get_registry_from_entry(uuid=uuid)
        registry.del_entry(uuid)

    def update_paths(self, old_base_path: Path, new_base_path: Path) -> None:
        """Update all paths across all registries if they start with old_base_path.

        Replaces the old_base_path prefix with new_base_path.

        :param old_base_path: The absolute base path prefix to find
        :param new_base_path: The absolute base path prefix to replace with
        :raises OSError: If path resolution fails
        :raises ValueError: If path operations fail
        """

        # Ensure paths are absolute and resolved for reliable comparison
        try:
            old_resolved = old_base_path.resolve()
            new_resolved = new_base_path.resolve()
        except OSError as e:
            logger.error(f'Error resolving paths for update: {e}. Aborting path update.')
            raise

        for registry in self.registries.values():
            for uuid, entry in registry.entries.items():
                # Update entry.path
                try:
                    resolved_entry_path = entry.path.resolve()
                    if resolved_entry_path.is_relative_to(old_resolved):
                        relative_part = resolved_entry_path.relative_to(old_resolved)
                        new_path = new_resolved / relative_part
                        if entry.path != new_path:
                            entry.path = new_path
                except (OSError, ValueError) as e:
                    logger.warning(f'Could not compare/update primary path for {uuid}: {entry.path}. Error: {e}')
                    raise

                # Update entry.symlinks
                updated_symlinks = []
                for symlink_path in entry.symlinks:
                    try:
                        resolved_symlink = symlink_path.resolve()
                        if resolved_symlink.is_relative_to(old_resolved):
                            relative_part = resolved_symlink.relative_to(old_resolved)
                            new_symlink = new_resolved / relative_part
                            updated_symlinks.append(new_symlink)
                        else:
                            updated_symlinks.append(symlink_path)
                    except (OSError, ValueError) as e:
                        logger.warning(f'Could not compare/update symlink for {uuid}: {symlink_path}. Error: {e}')
                        raise

                entry.symlinks = updated_symlinks

                # Update entry.duplicates
                updated_duplicates = []
                for duplicate_path in entry.duplicates:
                    try:
                        resolved_duplicate = duplicate_path.resolve()
                        if resolved_duplicate.is_relative_to(old_resolved):
                            relative_part = resolved_duplicate.relative_to(old_resolved)
                            new_duplicate = new_resolved / relative_part
                            updated_duplicates.append(new_duplicate)
                        else:
                            updated_duplicates.append(duplicate_path)
                    except (OSError, ValueError) as e:
                        logger.warning(f'Could not compare/update duplicate for {uuid}: {duplicate_path}. Error: {e}')
                        raise  # Add this line to be consistent with primary path handling

                entry.duplicates = updated_duplicates

    def set_current_mapping(self, current_mapping: GroupNodeMapping) -> None:
        """Set the current mapping to be saved to the JSON log file.

        :param current_mapping: Instance of ``GroupNodeMapping`` obtained from the current state of AiiDA's DB
        """
        self.current_mapping = current_mapping

    def iter_by_type(
        self,
    ) -> Generator[
        tuple[Literal['calculations'], DumpRegistry]
        | tuple[Literal['workflows'], DumpRegistry]
        | tuple[Literal['groups'], DumpRegistry]
    ]:
        """Iterate over node registries

        :yield: Tuple with the registry key string Literal and the corresponding ``DumpRegistry``
        """
        yield ('calculations', self.registries['calculations'])
        yield ('workflows', self.registries['workflows'])
        yield ('groups', self.registries['groups'])

    def _serialize_registry(self, registry: DumpRegistry) -> Dict[str, Dict[str, Any]]:
        """Serialize log entries to a dictionary format with paths relative to the dump base_output_path.

        :param registry: Instance of the ``DumpRegistry`` to be serialized
        :return: Serialized ``DumpRegistry`` dictionary representation
        :raises ValueError: If any path cannot be made relative to base_output_path
        """
        serialized = {}
        for uuid, entry in registry.entries.items():
            try:
                entry_dict = entry.to_dict()

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
                serialized[uuid] = entry_dict

            except ValueError as e:
                msg = (
                    f'Path {entry.path} or its links/duplicates not relative to {self.dump_paths.base_output_path}. '
                    f'Error: {e}'
                )
                logger.error(msg)
                raise

        return serialized

    def _deserialize_registry(self, data: Dict[str, Dict[str, Any]]) -> DumpRegistry:
        """Deserialize log entries using ``DumpRecord.from_dict`` and make paths absolute for internal handling.

        :param data: Serialized dictionary with UUIDs as keys and entry data as values
        :return: DumpRegistry instance with deserialized entries
        :raises ValueError: If deserialization fails or path operations fail
        """
        registry = DumpRegistry()
        for uuid, entry_data in data.items():
            if 'path' in entry_data:
                try:
                    # Use from_dict to get all fields correctly
                    dump_record = DumpRecord.from_dict(entry_data)
                    # Make paths absolute based on dump_paths.base_output_path
                    dump_record.path = self.dump_paths.base_output_path / dump_record.path
                    dump_record.symlinks = [self.dump_paths.base_output_path / p for p in dump_record.symlinks]
                    dump_record.duplicates = [self.dump_paths.base_output_path / p for p in dump_record.duplicates]

                    registry.add_entry(uuid, dump_record)
                except Exception as e:
                    logger.error(f'Failed to deserialize entry for UUID {uuid}: {e}')
                    raise

        return registry

    def _get_registry_from_entry(self, uuid: str) -> DumpRegistry:
        """Find registry that contains the given UUID.

        :param uuid: The UUID for which the registry should be found
        :raises ValueError: If UUID not contained in any registry
        :return: The retrieved ``DumpRegistry`` instance
        """
        for registry in self.registries.values():
            if uuid in registry.entries:
                return registry
        msg = f'UUID `{uuid}` not contained in any registry.'
        raise ValueError(msg)
