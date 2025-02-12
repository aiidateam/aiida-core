###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import json
from dataclasses import dataclass, field, fields
from datetime import datetime
from pathlib import Path
from typing import Collection


@dataclass
class DumpLog:
    """Represents a single dump log entry."""

    # TODO: Possibly add `node_type` or something similar here

    path: Path
    time: datetime
    links: list[Path] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {'path': str(self.path), 'time': self.time.isoformat(), 'links': [str(link) for link in self.links]}

    @classmethod
    def from_dict(cls, data: dict) -> 'DumpLog':
        return cls(
            path=Path(data['path']),
            time=datetime.fromisoformat(data['time']),
            links=[Path(link) for link in data.get('links', [])],
        )


@dataclass
class DumpLogStore:
    """A store for DumpLog entries, indexed by UUID."""

    entries: dict[str, DumpLog] = field(default_factory=dict)

    # TODO: If I support keeping track of the symlinks, possibly should implement extending them here
    def add_entry(self, uuid: str, entry: DumpLog) -> None:
        """Add a single entry to the container."""
        self.entries[uuid] = entry

    def add_entries(self, entries: dict[str, DumpLog]) -> None:
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

    def get_entry(self, uuid: str) -> DumpLog | None:
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
    def from_dict(cls, data: dict) -> 'DumpLogStore':
        store = cls()
        store.entries = {uuid: DumpLog.from_dict(entry) for uuid, entry in data.items()}
        return store


@dataclass
class DumpLogStoreCollection:
    """Represents the entire log, with calculations and workflows (will be extended with Data)."""

    calculations: DumpLogStore
    workflows: DumpLogStore


class DumpLogger:
    """Main logger class using dataclasses for better structure."""

    DUMP_LOG_FILE: str = '.dump_log.json'
    _instance: 'DumpLogger | None' = None  # Class-level singleton instance

    # TODO: Possibly add `get_calculations` and `get_workflows` as convenience methods

    def __new__(cls, *args, **kwargs):
        """Override __new__ to ensure only one instance of DumpLogger."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        dump_parent_path: Path | None = None,
        calculations: DumpLogStore | None = None,
        workflows: DumpLogStore | None = None,
        # counter: int = 0,
    ) -> None:
        # Ensure __init__ is only called once
        if hasattr(self, '_initialized') and self._initialized:
            return  # Skip reinitialization

        self.dump_parent_path = dump_parent_path or Path.cwd()
        self.calculations = calculations or DumpLogStore()
        self.workflows = workflows or DumpLogStore()
        # self.counter = counter

        # Mark the object as initialized
        self._initialized = True

    @property
    def log_file_path(self) -> Path:
        """Get the path to the dump file."""
        return self.dump_parent_path / self.DUMP_LOG_FILE

    def add_entry(self, store: DumpLogStore, uuid: str, entry: DumpLog) -> None:
        store.add_entry(uuid, entry)

    def del_entry(self, store: DumpLogStore, uuid: str) -> bool:
        return store.del_entry(uuid)

    @property
    def log(self) -> DumpLogStoreCollection:
        """Retrieve the current state of the log as a dataclass."""
        return DumpLogStoreCollection(calculations=self.calculations, workflows=self.workflows)

    def save_log(self) -> None:
        """Save the log to a JSON file."""

        def serialize_logs(container: DumpLogStore) -> dict:
            serialized = {}
            for uuid, entry in container.entries.items():
                serialized[uuid] = {'path': str(entry.path), 'time': entry.time.isoformat()}
            return serialized

        log_dict = {
            'calculations': serialize_logs(self.calculations),
            'workflows': serialize_logs(self.workflows),
        }

        with self.log_file_path.open('w', encoding='utf-8') as f:
            json.dump(log_dict, f, indent=4)

    def __enter__(self) -> 'DumpLogger':
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.save_log()

    @classmethod
    def from_file(cls, dump_parent_path: Path) -> 'DumpLogger':
        """Alternative constructor to load from an existing JSON file."""
        instance = cls(dump_parent_path=dump_parent_path)

        if not instance.log_file_path.exists():
            return instance

        try:
            with instance.log_file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)

            def deserialize_logs(category_data: dict) -> DumpLogStore:
                container = DumpLogStore()
                for uuid, entry in category_data.items():
                    container.add_entry(
                        uuid, DumpLog(path=Path(entry['path']), time=datetime.fromisoformat(entry['time']))
                    )
                return container

            instance.calculations = deserialize_logs(data['calculations'])
            instance.workflows = deserialize_logs(data['workflows'])

        except (json.JSONDecodeError, OSError):
            raise

        return instance

    def find_store_by_uuid(self, uuid: str) -> DumpLogStore | None:
        """Find the store that contains the given UUID."""
        # Iterate over the fields of the DumpLogStoreCollection dataclass for generality
        for field_ in fields(self.log):
            store = getattr(self.log, field_.name)
            if uuid in store.entries:
                return store
        return None
