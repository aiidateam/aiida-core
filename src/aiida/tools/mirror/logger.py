###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import json
from collections.abc import Collection
from dataclasses import dataclass, field, fields
from datetime import datetime
from pathlib import Path

from aiida.common.exceptions import NotExistent
from aiida.tools.mirror.utils import MirrorPaths

# TODO: Possibly mirror hierarchy of mirrored directory inside json file
# TODO: Currently, json file has only top-level "groups", "workflows", and "calculations"
# NOTE: Could use MirrorLogger also as container for orm.Nodes, that should be dumped
# NOTE: Should MirrorLogger be not provided (None), or should it rather just be empty with no entries
# NOTE: Is on `save_log` again the whole history being written to disk? Ideally, this would be incremental


@dataclass
class MirrorLog:
    """Represents a single dump log entry."""

    # TODO: Possibly add `node_type` or something similar here

    path: Path
    time: datetime
    links: list[Path] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'path': str(self.path),
            'time': self.time.isoformat(),
            'links': [str(link) for link in self.links],
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MirrorLog':
        return cls(
            path=Path(data['path']),
            time=datetime.fromisoformat(data['time']),
            links=[Path(link) for link in data.get('links', [])],
        )


@dataclass
class MirrorLogStore:
    """A store for MirrorLog entries, indexed by UUID."""

    entries: dict[str, MirrorLog] = field(default_factory=dict)

    # TODO: If I support keeping track of the symlinks, possibly should implement extending them here
    def add_entry(self, uuid: str, entry: MirrorLog) -> None:
        """Add a single entry to the container."""
        self.entries[uuid] = entry

    def add_entries(self, entries: dict[str, MirrorLog]) -> None:
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

    def get_entry(self, uuid: str) -> MirrorLog | None:
        """Retrieve a single entry by UUID."""
        return self.entries.get(uuid)

    def __len__(self) -> int:
        """Return the number of entries in the container."""
        return len(self.entries)

    def __iter__(self):
        """Iterate over all entries."""
        return iter(self.entries.items())

    def to_dict(self) -> dict:
        return {uuid: entry.to_dict() for uuid, entry in self.entries.items()}

    @classmethod
    def from_dict(cls, data: dict) -> 'MirrorLogStore':
        store = cls()
        store.entries = {uuid: MirrorLog.from_dict(entry) for uuid, entry in data.items()}
        return store


@dataclass
class MirrorLogStoreCollection:
    """Represents the entire log, with calculations and workflows (will be extended with Data)."""

    calculations: MirrorLogStore
    workflows: MirrorLogStore
    groups: MirrorLogStore
    data: MirrorLogStore


class MirrorLogger:
    """Main Logger class for data mirroring."""

    MIRROR_LOG_FILE: str = '.mirror_log.json'

    def __init__(
        self,
        mirror_paths: MirrorPaths,
        calculations: MirrorLogStore | None = None,
        workflows: MirrorLogStore | None = None,
        groups: MirrorLogStore | None = None,
        data: MirrorLogStore | None = None,
    ) -> None:
        self.mirror_paths = mirror_paths
        self.calculations = calculations or MirrorLogStore()
        self.workflows = workflows or MirrorLogStore()
        self.groups = groups or MirrorLogStore()
        self.data = data or MirrorLogStore()

    @property
    def log_file_path(self) -> Path:
        """Get the path to the dump file."""
        return self.mirror_paths.parent / self.mirror_paths.child / self.MIRROR_LOG_FILE

    def add_entry(self, store: MirrorLogStore, uuid: str, entry: MirrorLog) -> None:
        store.add_entry(uuid, entry)

    def del_entry(self, store: MirrorLogStore, uuid: str) -> bool:
        return store.del_entry(uuid)

    @property
    def log(self) -> MirrorLogStoreCollection:
        """Retrieve the current state of the log as a dataclass."""
        return MirrorLogStoreCollection(
            calculations=self.calculations,
            workflows=self.workflows,
            groups=self.groups,
            data=self.data,
        )

    def save_log(self) -> None:
        """Save the log to a JSON file."""

        def serialize_logs(container: MirrorLogStore) -> dict:
            serialized = {}
            for uuid, entry in container.entries.items():
                serialized[uuid] = {
                    'path': str(entry.path),
                    'time': entry.time.isoformat(),
                    'links': [str(link) for link in entry.links],
                }
            return serialized

        log_dict = {
            'calculations': serialize_logs(self.calculations),
            'workflows': serialize_logs(self.workflows),
            'groups': serialize_logs(self.groups),
            'data': serialize_logs(self.data),
        }

        # if not self.log_file_path.is_file():

        with self.log_file_path.open('w', encoding='utf-8') as f:
            json.dump(log_dict, f, indent=4)

    def __enter__(self) -> 'MirrorLogger':
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.save_log()

    @classmethod
    def from_file(cls, mirror_paths: MirrorPaths) -> 'MirrorLogger':
        """Alternative constructor to load from an existing JSON file."""
        instance = cls(mirror_paths=mirror_paths)

        if not instance.log_file_path.exists():
            return instance

        try:
            with instance.log_file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)

            def deserialize_logs(category_data: dict) -> MirrorLogStore:
                container = MirrorLogStore()
                for uuid, entry in category_data.items():
                    container.add_entry(
                        uuid,
                        MirrorLog(
                            path=Path(entry['path']),
                            time=datetime.fromisoformat(entry['time']),
                            links=[Path(p) for p in entry['links']],
                        ),
                    )

                return container

            instance.calculations = deserialize_logs(data['calculations'])
            instance.workflows = deserialize_logs(data['workflows'])
            instance.groups = deserialize_logs(data['groups'])
            # instance.data = deserialize_logs(data['data'])

        except (json.JSONDecodeError, OSError):
            raise

        return instance

    def get_store_by_uuid(self, uuid: str) -> MirrorLogStore:
        """Find the store that contains the given UUID."""
        # Iterate over the fields of the MirrorLogStoreCollection dataclass for generality
        # TODO: Add error handling for wrong UUID
        for field_ in fields(self.log):
            store = getattr(self.log, field_.name)
            if uuid in store.entries:
                return store

        msg = f'No corresponding `MirrorLogStore` found for UUID: `{uuid}`.'
        raise NotExistent(msg)

    def get_path_by_uuid(self, uuid: str) -> Path | None:
        """Find the store that contains the given UUID."""
        # Iterate over the fields of the MirrorLogStoreCollection dataclass for generality

        try:
            current_store = self.get_store_by_uuid(uuid=uuid)
        except NotExistent as exc:
            raise NotExistent(exc.args[0]) from exc
        try:
            path = current_store.entries[uuid].path
            return path
        except KeyError as exc:
            msg = f'UUID: `{uuid}` not contained in store `{current_store}`.'
            raise KeyError(msg) from exc
        except:
            # For debugging

            raise

    def to_dict(self) -> dict:
        """
        Convert the MirrorLogger state to a dictionary format.

        Returns:
            dict: A dictionary representation of the MirrorLogger state,
                containing all calculations, workflows, groups, and data entries.
        """

        def serialize_logs(container: MirrorLogStore) -> dict:
            return container.to_dict()

        return {
            'calculations': serialize_logs(self.calculations),
            'workflows': serialize_logs(self.workflows),
            'groups': serialize_logs(self.groups),
            'data': serialize_logs(self.data),
        }
