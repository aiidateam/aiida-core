from __future__ import annotations

import pathlib
from rich.console import Console
from rich.table import Table
import sys


class AbstractDumper:
    def __init__(
        self,
        parent_path: str | pathlib.Path = pathlib.Path(),
        overwrite: bool = False,
        incremental: bool = False,
        also_raw: bool = False,
        also_rich: bool = False,
        dry_run: bool = False,
        rich_kwargs: dict = {}
    ):
        self.parent_path = parent_path
        self.overwrite = overwrite
        self.incremental = incremental
        self.also_raw = also_raw
        self.also_rich = also_rich
        self.dry_run = dry_run
        self.rich_kwargs = rich_kwargs

    def pretty_print(self, also_private: bool = True, also_dunder: bool = False):
        console = Console()
        table = Table(title=f"Attributes and Methods of {self.__class__.__name__}")

        # Adding columns to the table
        table.add_column("Name", justify="left")
        table.add_column("Type", justify="left")
        table.add_column("Value", justify="left")

        # Lists to store attributes and methods
        entries = []

        # Iterate over the class attributes and methods
        for attr_name in dir(self):
            # Exclude private attributes and dunder methods
            if not also_private and not also_dunder:
                if not (attr_name.startswith('_') or attr_name.endswith('_')):
                    attr_value = getattr(self, attr_name)
                    entry_type = "Attribute" if not callable(attr_value) else "Method"
                    entries.append((attr_name, entry_type, str(attr_value)))

            if not also_private:
                if attr_name.startswith('__'):
                    attr_value = getattr(self, attr_name)
                    entry_type = "Attribute" if not callable(attr_value) else "Method"
                    entries.append((attr_name, entry_type, str(attr_value)))

            if not also_dunder:
                if not attr_name.startswith('__'):
                    attr_value = getattr(self, attr_name)
                    entry_type = "Attribute" if not callable(attr_value) else "Method"
                    entries.append((attr_name, entry_type, str(attr_value)))
            else:
                attr_value = getattr(self, attr_name)
                entry_type = "Attribute" if not callable(attr_value) else "Method"
                entries.append((attr_name, entry_type, str(attr_value)))


        # Sort entries: attributes first, then methods
        entries.sort(key=lambda x: (x[1] == "Method", x[0]))

        # Add sorted entries to the table
        for name, entry_type, value in entries:
            table.add_row(name, entry_type, value)

        # Print the formatted table
        console.print(table)

    @staticmethod
    def check_storage_size_user():
        from aiida.manage.manager import get_manager

        manager = get_manager()
        storage = manager.get_profile_storage()

        data = storage.get_info(detailed=True)
        repository_data = data['repository']['Size (MB)']
        total_size_gb = sum(repository_data.values()) / 1024
        if total_size_gb > 10:
            user_input = (
                input('Repository size larger than 10gb. Do you still want to dump the profile data? (y/N): ')
                .strip()
                .lower()
            )

            if user_input != 'y':
                sys.exit()

