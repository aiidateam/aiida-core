import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TypeAlias


@dataclass
class DumpLog:
    """Represents a single dump log entry."""

    path: Path
    time: datetime


DumpDict: TypeAlias = dict[str, DumpLog]


class DumpLogger:
    """Main logger class using dataclasses for better structure."""

    DUMP_FILE: str = '.dump_log.json'

    def __init__(
        self,
        dump_parent_path: Path | None = None,
        calculations: DumpDict | None = None,
        workflows: DumpDict | None = None,
        counter: int = 0,
    ) -> None:
        self.dump_parent_path = dump_parent_path or Path.cwd()
        self.calculations = calculations or {}
        self.workflows = workflows or {}
        self.counter = 0

    @property
    def dump_file(self) -> Path:
        """Get the path to the dump file."""
        return self.dump_parent_path / self.DUMP_FILE

    def update_calculations(self, new_calculations: DumpDict) -> None:
        """Update the calculations log."""
        self.calculations.update(new_calculations)
        self.counter += len(new_calculations)

    def update_workflows(self, new_workflows: DumpDict) -> None:
        """Update the workflows log."""
        self.workflows.update(new_workflows)
        self.counter += len(new_workflows)

    def get_log(self) -> dict[str, DumpDict]:
        """Retrieve the current state of the log."""
        return {'calculations': self.calculations, 'workflows': self.workflows}

    def save_log(self) -> None:
        """Save the log to a JSON file."""

        def serialize_logs(logs: DumpDict) -> dict:
            serialized = {}
            for uuid, entry in logs.items():
                serialized[uuid] = {'path': str(entry.path), 'time': entry.time.isoformat()}
            return serialized

        log_dict = {
            'calculations': serialize_logs(self.calculations),
            'workflows': serialize_logs(self.workflows),
        }

        with self.dump_file.open('w', encoding='utf-8') as f:
            json.dump(log_dict, f, indent=4)

    @classmethod
    def from_file(cls, dump_parent_path: Path) -> 'DumpLogger':
        """Alternative constructor to load from an existing JSON file."""
        instance = cls(dump_parent_path=dump_parent_path)

        if not instance.dump_file.exists():
            return instance

        try:
            with instance.dump_file.open('r', encoding='utf-8') as f:
                data = json.load(f)

            def deserialize_logs(category_data: dict) -> DumpDict:
                deserialized = {}
                for uuid, entry in category_data.items():
                    deserialized[uuid] = DumpLog(path=Path(entry['path']), time=datetime.fromisoformat(entry['time']))
                return deserialized

            instance.calculations = deserialize_logs(data['calculations'])
            instance.workflows = deserialize_logs(data['workflows'])

        except (json.JSONDecodeError, OSError):
            raise

        return instance
