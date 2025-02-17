###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions for dumping features."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import NamedTuple, cast

from aiida import orm
from aiida.common.log import AIIDA_LOGGER

__all__ = (
    'NodeDumpKeyMapper',
    'ProcessesToDumpContainer',
    'filter_nodes_last_dump_time',
    'prepare_dump_path',
    'safe_delete_dir',
)

logger = AIIDA_LOGGER.getChild('tools.dumping')


class ProcessesToDumpContainer(NamedTuple):
    calculations: list[orm.CalculationNode]
    workflows: list[orm.WorkflowNode]

    @property
    def is_empty(self) -> bool:
        """Check if there are any processes to dump."""
        return len(self.calculations) == 0 and len(self.workflows) == 0


class NodeDumpKeyMapper:
    calculation_key: str = 'calculations'
    workflow_key: str = 'workflows'

    @classmethod
    def get_key_from_node(cls, node: orm.Node) -> str:
        if isinstance(node, orm.CalculationNode):
            return cls.calculation_key
        elif isinstance(node, orm.WorkflowNode):
            return cls.workflow_key
        else:
            msg = f'Dumping not implemented yet for node type: {type(node)}'
            raise NotImplementedError(msg)


def prepare_dump_path(
    path_to_validate: Path,
    overwrite: bool = False,
    incremental: bool = True,
    safeguard_file: str = '.aiida_node_metadata.yaml',
    verbose: bool = False,
) -> None:
    """Create default dumping directory for a given process node and return it as absolute path.

    :param validate_path: Path to validate for dumping.
    :param safeguard_file: Dumping-specific file that indicates that the directory indeed originated from a `verdi ...
        dump` command to avoid accidentally deleting wrong directory.
        Default: `.aiida_node_metadata.yaml`
    :return: The absolute created dump path.
    :raises ValueError: If both `overwrite` and `incremental` are set to True.
    :raises FileExistsError: If a file or non-empty directory exists at the given path and none of `overwrite` or
        `incremental` are enabled.
    :raises FileNotFoundError: If no `safeguard_file` is found."""

    if overwrite and incremental:
        msg = 'Both overwrite and incremental set to True. Only specify one.'
        raise ValueError(msg)

    if path_to_validate.is_file():
        msg = f'A file at the given path `{path_to_validate}` already exists.'
        raise FileExistsError(msg)

    # Handle existing directory
    if path_to_validate.is_dir():
        is_empty = not any(path_to_validate.iterdir())

        # Case 1: Non-empty directory and overwrite is False
        if not is_empty and not overwrite:
            if not incremental:
                msg = f'Path `{path_to_validate}` already exists, and neither overwrite nor incremental is enabled.'
                raise FileExistsError(msg)

        # Case 2: Non-empty directory, overwrite is True
        if not is_empty and overwrite:
            safe_delete_dir(
                path_to_validate=path_to_validate,
                safeguard_file=safeguard_file,
                verbose=verbose,
            )

    # Re-create directory, as both shutil.rmtree and `_delete_dir_recursively` delete the original dir
    path_to_validate.mkdir(exist_ok=True, parents=True)
    (path_to_validate / safeguard_file).touch()


def safe_delete_dir(
    path_to_validate: Path,
    safeguard_file: str = '.aiida_node_metadata.yaml',
    verbose: bool = False,
) -> None:
    """Also deletes the top-level directory itself."""

    if not path_to_validate.exists():
        return

    is_empty = not any(path_to_validate.iterdir())
    if is_empty:
        path_to_validate.rmdir()
        return

    safeguard_exists = (path_to_validate / safeguard_file).is_file()

    if safeguard_exists:
        if verbose:
            logger.report(str(path_to_validate))
            msg = '`--overwrite` option selected. Will recreate directory.'
            logger.report(msg)
        try:
            _delete_dir_recursive(path_to_validate)
            # shutil.rmtree(path_to_validate)
        except OSError:
            # `shutil.rmtree` fails for symbolic links with
            # OSError: Cannot call rmtree on a symbolic link
            _delete_dir_recursive(path_to_validate)

    else:
        msg = (
            f'Path `{path_to_validate}` exists without safeguard file `{safeguard_file}`. '
            f'Not removing because path might be a directory not created by AiiDA.'
        )
        raise FileNotFoundError(msg)


def _delete_dir_recursive(path):
    """
    Delete folder, sub-folders and files.
    Implementation taken from: https://stackoverflow.com/a/70285390/9431838
    """
    for f in path.glob('**/*'):
        if f.is_symlink():
            f.unlink(missing_ok=True)  # missing_ok is added in python 3.8
        elif f.is_file():
            f.unlink()
        elif f.is_dir():
            try:
                f.rmdir()  # delete empty sub-folder
            except OSError:  # sub-folder is not empty
                _delete_dir_recursive(f)  # recurse the current sub-folder
            except Exception as exception:  # capture other exception
                print(f'exception name: {exception.__class__.__name__}')
                print(f'exception msg: {exception}')

    try:
        path.rmdir()  # time to delete an empty folder
    except NotADirectoryError:
        path.unlink()  # delete folder even if it is a symlink, linux
    except Exception as exception:
        print(f'exception name: {exception.__class__.__name__}')
        print(f'exception msg: {exception}')


def filter_nodes_last_dump_time(nodes: list[str], last_dump_time: datetime | None = None) -> list[str]:
    """Filter a list of nodes by the last dump time of the corresponding dumper.

    :param nodes: A list of node identifiers, which can be either UUIDs (str) or IDs (int).
    :param last_dump_time: Only include nodes dumped after this timestamp.
    :return: A list of node identifiers that have a dump time after the specified last_dump_time.
    """

    # TODO: Possibly directly use QueryBuilder filter. Though, `nodes` directly accessible from orm.Group.nodes
    if not nodes or last_dump_time is None:
        return nodes

    qb = orm.QueryBuilder().append(orm.Node, filters={'uuid': {'in': nodes}})
    nodes_orm: list[orm.Node] = cast(list[orm.Node], qb.all(flat=True))
    return [node.uuid for node in nodes_orm if node.mtime > last_dump_time]
