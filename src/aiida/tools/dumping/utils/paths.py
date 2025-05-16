###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

"""Path utility functions and classes for the dumping feature."""

# NOTE: Could manke many of the functions staticmethods of DumpPaths

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from aiida import orm
from aiida.common import timezone
from aiida.common.log import AIIDA_LOGGER
from aiida.manage.configuration import Profile
from aiida.tools.dumping.config import DumpMode

logger = AIIDA_LOGGER.getChild('tools.dumping.utils.paths')

__all__ = ('DumpPaths',)


@dataclass
class DumpPaths:
    parent: Path = field(default_factory=Path.cwd)
    child: Path = field(default_factory=lambda: Path('aiida-dump'))
    _top_level: Path | None = field(default=None, init=False, repr=False)

    safeguard_file = '.aiida_dump_safeguard'
    log_file: str = 'aiida_dump_log.json'
    config_file: str = 'aiida_dump_config.yaml'

    def __post_init__(self):
        # Set top_level during initialization if not provided
        # This should not change after construction, as it should always point at the top-level dump directory
        self._top_level = self.parent / self.child

    @property
    def top_level(self) -> Path:
        """Returns the top level path, guaranteed to be non-None."""
        assert self._top_level is not None
        return self._top_level

    @classmethod
    def from_path(cls, path: Path):
        return cls(parent=path.parent, child=Path(path.name))

    @property
    def absolute(self) -> Path:
        """Returns the absolute path by joining parent and child."""
        return self.parent / self.child

    @property
    def safeguard_path(self) -> Path:
        """Returns the relative path to a safeguard file."""
        return self.absolute / self.safeguard_file

    @property
    def log_path(self) -> Path:
        """Returns the path of the logger JSON."""
        return self.absolute / self.log_file

    # NOTE: Should this return a new instance?
    def extend_paths(self, subdir: str) -> DumpPaths:
        """
        Creates a new DumpPaths instance with an additional subdirectory.

        Args:
            subdir: The name of the subdirectory to add

        Returns:
            A new DumpPaths instance with the updated path structure
        """
        return DumpPaths(parent=self.absolute, child=Path(subdir))

    @property
    def config_path(self) -> Path:
        """Returns the path of the top-level config YAML."""
        assert self.top_level is not None
        return self.top_level / self.config_file

    @staticmethod
    def _prepare_dump_path(
        path_to_validate: Path,
        dump_mode: DumpMode,
        safeguard_file: str = safeguard_file,
        # top_level_caller: bool = True,
    ) -> None:
        # TODO: Add an option to clean the path here
        """Create default dumping directory for a given process node and return it as absolute path.

        :param validate_path: Path to validate for dumping.
        :param safeguard_file: Dumping-specific file that indicates that the directory originated from AiiDA's
            dump` command to avoid accidentally deleting wrong directory.
        :return: The absolute created dump path.
        :raises ValueError: If both `overwrite` and `incremental` are set to True.
        :raises FileExistsError: If a file or non-empty directory exists at the given path and none of `overwrite` or
            `incremental` are enabled.
        :raises FileNotFoundError: If no `safeguard_file` is found."""

        if path_to_validate.is_file():
            msg = f'A file at the given path `{path_to_validate}` already exists.'
            raise FileExistsError(msg)

        if not path_to_validate.is_absolute():
            msg = f'The path to validate must be an absolute path. Got `{path_to_validate}.'
            raise ValueError(msg)

        # Handle existing non-empty directory
        safeguard_path = path_to_validate / safeguard_file
        if path_to_validate.is_dir() and any(path_to_validate.iterdir()):
            # Check for safeguard first if directory is not empty
            if not safeguard_path.is_file():
                # If non-empty AND safeguard is missing, it's an error for OVERWRITE and INCREMENTAL
                if dump_mode in (DumpMode.OVERWRITE, DumpMode.INCREMENTAL):
                    msg = (
                        f'Path `{path_to_validate}` exists and is not empty, but safeguard file '
                        f'`{safeguard_file}` is missing. Cannot proceed in {dump_mode.name} mode '
                        f'to prevent accidental data modification/loss.'
                    )
                    logger.error(msg)
                    raise FileNotFoundError(msg)
                # For DRY_RUN, we might just log a warning or proceed silently
                # depending on desired dry-run feedback. Let's log for now.
                elif dump_mode == DumpMode.DRY_RUN:
                    logger.warning(
                        f'DRY RUN: Path `{path_to_validate}` exists, is not empty, and safeguard file '
                        f'`{safeguard_file}` is missing.'
                    )
            # Safeguard IS present and directory is non-empty
            elif dump_mode == DumpMode.OVERWRITE:
                DumpPaths._safe_delete_dir(
                    path=path_to_validate,
                    safeguard_file=safeguard_file,
                )

        # Check if path is symlink, otherwise `mkdir` fails
        if path_to_validate.is_symlink():
            return

        # Finally, (re-)create directory
        # Both shutil.rmtree and `_delete_dir_recursively` delete the original dir
        # If it already existed, e.g. in the `incremental` case, exist_ok=True
        path_to_validate.mkdir(exist_ok=True, parents=True)
        path_to_safeguard_file = path_to_validate / safeguard_file
        if not path_to_safeguard_file.is_file():
            path_to_safeguard_file.touch()

    @staticmethod
    def _safe_delete_dir(
        path: Path,
        safeguard_file: str = safeguard_file,
    ) -> None:
        """Safely delete a directory and its contents if it contains the safeguard file.
        Uses shutil.rmtree for robust deletion. Also deletes the top-level directory itself.
        """
        if not path.exists():
            logger.debug(f"Path '{path}' does not exist, nothing to delete.")
            return

        # If it's not a directory (e.g., a file or a symlink), handle differently
        if not path.is_dir():
            if path.is_symlink():
                logger.debug(f"Path '{path}' is a symlink, unlinking.")
                path.unlink()  # missing_ok=True requires Python 3.8+
            else:
                logger.debug(f"Path '{path}' is a file, unlinking.")
                path.unlink()  # missing_ok=True requires Python 3.8+
            return

        # Check if directory is empty *before* safeguard check
        is_empty = not any(path.iterdir())
        if is_empty:
            logger.debug(f"Path '{path}' is an empty directory, removing.")
            path.rmdir()
            return

        # Check for safeguard file existence
        safeguard_path = path / safeguard_file
        if not safeguard_path.is_file():
            msg = (
                f'Path `{path}` exists and is not empty, but safeguard file `{safeguard_file}` is missing. '
                f'Not removing directory to prevent accidental data loss.'
            )
            logger.error(msg)  # Log as error as this is a safety stop
            raise FileNotFoundError(msg)  # Raise exception to signal failure

        # Safeguard exists, proceed with deletion using shutil.rmtree
        logger.debug(f"Safeguard file found in '{path}'. Proceeding with recursive deletion.")
        try:
            shutil.rmtree(path)
            logger.debug(f"Successfully deleted directory tree: '{path}'")
        except OSError as e:
            # Catch potential errors during rmtree (e.g., permissions)
            logger.error(
                f"Error deleting directory tree '{path}' using shutil.rmtree: {e}",
                exc_info=True,
            )
            raise  # Re-raise the error after logging

    @staticmethod
    def _get_default_process_dump_path(
        process_node: orm.ProcessNode, prefix: str | None = None, append_pk: bool = True
    ) -> Path:
        """Simple helper function to generate the default parent-dumping directory if none given.

        This function is not called for the recursive sub-calls of `_dump_calculation` as it just creates the default
        parent folder for the dumping, if no name is given.

        :param process_node: The `ProcessNode` for which the directory is created.
        :return: The absolute default parent dump path.
        """

        path_entities = []

        if prefix is not None:
            path_entities += [prefix]

        if process_node.label:
            path_entities.append(process_node.label)
        elif process_node.process_label is not None:
            path_entities.append(process_node.process_label)
        elif process_node.process_type is not None:
            path_entities.append(process_node.process_type)

        if append_pk:
            path_entities += [str(process_node.pk)]
        return Path('-'.join(path_entities))

    @staticmethod
    def _get_default_profile_dump_path(
        profile: Profile, prefix: Optional[str] = None, appendix: Optional[str] = None
    ) -> Path:
        """_summary_

        :param profile: _description_
        :param prefix: _description_, defaults to "profile"
        :param appendix: _description_, defaults to "dump"
        :return: _description_
        """
        label_elements = []

        if prefix:
            label_elements.append(prefix)
        label_elements.append(profile.name)
        if appendix:
            label_elements.append(appendix)

        return Path('-'.join(label_elements))

    @staticmethod
    def _get_default_group_dump_path(
        group: orm.Group, prefix: Optional[str] = None, appendix: Optional[str] = None
    ) -> Path:
        label_elements = []

        if prefix:
            label_elements.append(prefix)
        label_elements.append(group.label)
        if appendix:
            label_elements.append(appendix)

        return Path('-'.join(label_elements))

    @staticmethod
    def _resolve_click_path_for_dump(
        entity: Profile | orm.ProcessNode | orm.Group, path: Path | None | str
    ) -> DumpPaths:
        if path:
            path = Path(path)
            if path.is_absolute():
                dump_sub_path = Path(path.name)
                dump_parent_path = path.parent
            else:
                dump_sub_path = path
                dump_parent_path = Path.cwd()
        else:
            # Use direct isinstance checks to determine which generator to use
            if isinstance(entity, Profile):
                dump_sub_path = DumpPaths._get_default_profile_dump_path(entity)
            elif isinstance(entity, orm.Group):
                dump_sub_path = DumpPaths._get_default_group_dump_path(entity)
            elif isinstance(entity, orm.ProcessNode):
                dump_sub_path = DumpPaths._get_default_process_dump_path(entity)
            else:
                raise ValueError

            dump_parent_path = Path.cwd()

        return DumpPaths(
            parent=dump_parent_path,
            child=dump_sub_path,
        )

    @staticmethod
    def _get_group_path(group: orm.Group | None, organize_by_groups: bool = True) -> Path:
        """Calculate and return the dump path for a specific group.

        :param group: _description_
        :param organize_by_groups: _description_, defaults to True
        :return: _description_
        """
        if organize_by_groups:
            if group:
                # Calculate the subpath based on the group's entry point
                group_entry_point = group.entry_point
                if group_entry_point is None:
                    group_subpath = Path(group.label)
                else:
                    group_entry_point_name = group_entry_point.name
                    if group_entry_point_name == 'core':
                        group_subpath = Path(f'{group.label}')
                    elif group_entry_point_name == 'core.import':
                        group_subpath = Path('import') / f'{group.label}'
                    else:
                        group_subpath = Path(*group_entry_point_name.split('.')) / f'{group.label}'

                # Hierarchical structure under 'groups/' using entry point/label
                group_path = Path('groups') / group_subpath
            else:
                group_path = Path('ungrouped')
        else:
            # Flat structure - return the main dump path
            group_path = Path('.')

        return group_path

    @staticmethod
    def _get_directory_stats(path: Path) -> tuple[datetime | None, int | None]:
        """
        Calculate the total size and last modification time of a directory's contents.

        Args:
            path: The directory path.

        Returns:
            A tuple containing:
                - datetime | None: The most recent modification time among all files/dirs,
                                made timezone-aware (UTC assumed if naive).
                - int | None: The total size in bytes of all files within the directory.
                            Returns None if the path doesn't exist or isn't a directory.
        """
        total_size = 0
        latest_mtime_ts = 0.0

        try:
            if not path.is_dir():
                logger.debug(f'Path {path} is not a directory, cannot calculate stats.')
                return None, None

            # Get mtime of the directory itself initially
            latest_mtime_ts = path.stat().st_mtime

            # Iterate through all files and directories recursively
            for entry in path.rglob('*'):
                try:
                    stat_info = entry.stat()
                    if entry.is_file():
                        total_size += stat_info.st_size
                    # Update latest mtime if this entry is newer
                    latest_mtime_ts = max(stat_info.st_mtime, latest_mtime_ts)
                except (OSError, FileNotFoundError) as stat_err:
                    # Ignore errors for files/dirs that might disappear during iteration
                    logger.debug(f'Could not stat entry {entry}: {stat_err}')

            # Convert the latest timestamp to a timezone-aware datetime object
            latest_mtime_dt = datetime.fromtimestamp(latest_mtime_ts)
            latest_mtime_aware = timezone.make_aware(latest_mtime_dt)  # Assumes local time if naive

            return latest_mtime_aware, total_size

        except (FileNotFoundError, PermissionError) as e:
            logger.error(f'Could not access path {path} to calculate stats: {e}')
            return None, None
        except Exception as e:
            logger.error(f'Unexpected error calculating stats for {path}: {e}', exc_info=True)
            return None, None
