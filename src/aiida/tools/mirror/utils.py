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

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

from aiida import load_profile, orm
from aiida.common.exceptions import NotExistent
from aiida.common.log import AIIDA_LOGGER
from aiida.manage.configuration import Profile
from aiida.tools.mirror.config import MirrorMode

if TYPE_CHECKING:
    from aiida.tools.mirror.logger import MirrorLogger

__all__ = (
    'MirrorPaths',
    'NodeMirrorKeyMapper',
    'do_filter_nodes',
    'get_group_subpath',
    'prepare_mirror_path',
    'safe_delete_dir',
)

logger = AIIDA_LOGGER.getChild('tools.mirror.utils')


class NodeMirrorKeyMapper:
    calculation_key: str = 'calculations'
    workflow_key: str = 'workflows'
    data_key: str = 'data'

    @classmethod
    def get_key_from_instance(cls, node_inst: orm.Node) -> str:
        match node_inst:
            case orm.CalculationNode():
                return cls.calculation_key
            case orm.WorkflowNode():
                return cls.workflow_key
            case orm.Data():
                return cls.data_key
            case _:
                msg = f'Mirroring not implemented yet for node type: {type(node_inst)}'
                raise NotImplementedError(msg)

    @classmethod
    def get_key_from_class(cls, node_type: type) -> str:
        if issubclass(node_type, orm.CalculationNode):
            return cls.calculation_key
        elif issubclass(node_type, orm.WorkflowNode):
            return cls.workflow_key
        elif issubclass(node_type, orm.Data):
            return cls.data_key
        else:
            msg = f'Mirroring not implemented yet for node type: {node_type}'
            raise NotImplementedError(msg)


# NOTE: Could also add logger and safeguard file path here
@dataclass
class MirrorPaths:
    parent: Path = Path.cwd
    child: Path = Path('aiida-mirror')

    @property
    def absolute(self) -> Path:
        """Returns the absolute path by joining parent and child."""
        return self.parent / self.child

    @property
    def safeguard_path(self) -> Path:
        """Returns the path to a safeguard file."""
        return self.absolute / '.aiida_safeguard'

    # NOTE: Should this return a new instance?
    def extend_paths(self, subdir: str) -> 'MirrorPaths':
        """
        Creates a new MirrorPaths instance with an additional subdirectory.

        Args:
            subdir: The name of the subdirectory to add

        Returns:
            A new MirrorPaths instance with the updated path structure
        """
        return MirrorPaths(parent=self.absolute, child=Path(subdir))

    # @property
    # def logger_path(self) -> Path:
    #     """Returns the path to a safeguard file."""
    #     return self.absolute / ".aiida_safeguard"

    # @property
    # def logger(self) -> logging.Logger:
    #     """Returns a logger specific to this dump path."""
    #     logger_name = f"mirror_paths.{self.parent.name}.{self.child.name}"
    #     return logging.getLogger(logger_name)


# class SafeguardFileMapping(Enum):
#     PROCESS = '.aiida_process_safeguard'
#     GROUP = '.aiida_group_safeguard'
#     PROFILE = '.aiida_profile_safeguard'


# NOTE: Could move to BaseMirror class
def prepare_mirror_path(
    path_to_validate: Path,
    mirror_mode: MirrorMode,
    safeguard_file: str,
    top_level_caller: bool = False,
) -> None:
    """Create default dumping directory for a given process node and return it as absolute path.

    :param validate_path: Path to validate for dumping.
    :param safeguard_file: Mirroring-specific file that indicates that the directory indeed originated from a `verdi ...
        dump` command to avoid accidentally deleting wrong directory.
        Default: `.aiida_node_metadata.yaml`
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

    # Additional logging for top-level directory
    # Don't want to repeat that for all sub-directories created during dumping
    if top_level_caller:
        if mirror_mode == MirrorMode.INCREMENTAL:
            msg = 'Incremental mirroring selected. Will update directory.'
        elif mirror_mode == MirrorMode.OVERWRITE:
            msg = 'Overwriting selected. Will clean directory first.'

        logger.report(msg)

    # Handle existing non-empty directory
    if path_to_validate.is_dir() and any(path_to_validate.iterdir()) and mirror_mode == MirrorMode.OVERWRITE:
        safe_delete_dir(
            path_to_validate=path_to_validate,
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


def safe_delete_dir(
    path_to_validate: Path,
    safeguard_file: str,
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
        try:
            _delete_dir_recursive(path_to_validate)
            # shutil.rmtree(path_to_validate)
        except OSError:
            # `shutil.rmtree` fails for symbolic links with
            # OSError: Cannot call rmtree on a symbolic link
            _delete_dir_recursive(path_to_validate)

    else:
        msg = (
            f'Path `{path_to_validate.name}` exists without safeguard file `{safeguard_file}`. '
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


def do_filter_nodes(nodes: list[str], last_dump_time: datetime | None = None) -> list[str]:
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


def load_given_group(group: orm.Group | str) -> orm.Group:
    """Validate the given group identifier.

    :param group: The group identifier to validate.
    :return: Insance of ``orm.Group``.
    :raises NotExistent: If no ``orm.Group`` can be loaded for a given label.
    """

    if isinstance(group, str):
        try:
            return orm.load_group(group)
        # `load_group` raises the corresponding errors
        except NotExistent:
            raise
        except:
            raise

    elif isinstance(group, orm.Group):
        return group


def generate_process_default_mirror_path(
    process_node: orm.ProcessNode, prefix: str | None = 'dump', append_pk: bool = True
) -> Path:
    """Simple helper function to generate the default parent-dumping directory if none given.

    This function is not called for the recursive sub-calls of `_dump_calculation` as it just creates the default
    parent folder for the dumping, if no name is given.

    :param process_node: The `ProcessNode` for which the directory is created.
    :return: The absolute default parent dump path.
    """

    entities_to_dump = []

    # No '' and None
    if prefix is not None:
        entities_to_dump += [prefix]

    try:
        if process_node.process_label is not None:
            entities_to_dump.append(process_node.process_label)
    except AttributeError:
        # This case came up during testing, not sure how relevant it actually is
        if process_node.process_type is not None:
            entities_to_dump.append(process_node.process_type)

    if append_pk:
        entities_to_dump += [str(process_node.pk)]

    return Path('-'.join(entities_to_dump))


def generate_profile_default_mirror_path(
    profile: Profile = load_profile(), prefix: str = 'profile', appendix: str = 'mirror'
) -> Path:
    return Path(f'{prefix}-{profile.name}-{appendix}')


def generate_group_default_mirror_path(group: orm.Group, prefix: str = 'group', appendix: str = 'mirror') -> Path:
    # TODO: Or, make sure mirror not in the group name?
    if 'group' in group.label:
        if appendix == 'group' and prefix != 'group':
            label_elements = [prefix, group.label]
        elif prefix == 'group' and appendix != 'group':
            label_elements = [group.label, appendix]
        elif prefix == 'group' and appendix == 'group':
            label_elements = [group.label]
        else:
            label_elements = [prefix, group.label, appendix]

    elif 'mirror' in group.label:
        if appendix == 'mirror' and prefix != 'mirror':
            label_elements = [prefix, group.label]
        elif prefix == 'mirror' and appendix != 'mirror':
            label_elements = [group.label, appendix]
        elif prefix == 'mirror' and appendix == 'mirror':
            label_elements = [group.label]
        else:
            label_elements = [prefix, group.label, appendix]

    else:
        label_elements = [prefix, group.label, appendix]

    return_str = '-'.join(label_elements)

    return Path(return_str)


def resolve_click_path_for_mirror(
    path: Path | None | str, entity: orm.ProcessNode | orm.Group | Profile
) -> MirrorPaths:
    _entity_mirror_functions = {
        orm.ProcessNode: generate_process_default_mirror_path,
        orm.Group: generate_group_default_mirror_path,
        Profile: generate_profile_default_mirror_path,
    }

    for entity_class, dump_path_generator in _entity_mirror_functions.items():
        if isinstance(entity, entity_class):
            if path:
                path = Path(path)
                if path.is_absolute():
                    dump_sub_path = Path(path.name)
                    dump_parent_path = path.parent
                else:
                    dump_sub_path = path
                    dump_parent_path = Path.cwd()
            else:
                dump_sub_path = dump_path_generator(entity)
                dump_parent_path = Path.cwd()

            return MirrorPaths(
                parent=dump_parent_path,
                child=dump_sub_path,
            )

    supported_types = ', '.join(cls.__name__ for cls in _entity_mirror_functions)
    raise ValueError(f"Unsupported entity type '{type(entity).__name__}'. Supported types: {supported_types}.")


def delete_missing_node_dir(mirror_logger: 'MirrorLogger', to_delete_uuid: str) -> None:
    # TODO: Possibly make a delete method for the path and the log, and then call that in the loop

    current_store = mirror_logger.get_store_by_uuid(uuid=to_delete_uuid)
    if not current_store:
        return

    # ! Cannot load the node via its UUID here and use the type to get the correct store, as the Node is deleted
    # ! from the DB. Should find a better solution

    # breakpoint()
    path_to_delete = mirror_logger.get_path_by_uuid(uuid=to_delete_uuid)
    if path_to_delete is not None:
        try:
            safe_delete_dir(
                path_to_validate=path_to_delete,
                safeguard_file='.aiida_node_metadata.yaml',
                verbose=False,
            )
            current_store.del_entry(uuid=to_delete_uuid)
        except:
            raise
