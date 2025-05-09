###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Dumper facades serving as public API for data dumping feature."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Type

from aiida import orm
from aiida.common.exceptions import NotExistent
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.config import DumpConfig
from aiida.tools.dumping.engine import DumpEngine
from aiida.tools.dumping.utils.paths import DumpPaths

logger = AIIDA_LOGGER.getChild('tools.dumping.facades')


class ProcessDumper:
    """Dumps data of a single ProcessNode."""

    @classmethod
    def from_config(
        cls,
        process: orm.ProcessNode | int | str,
        config_path: str | Path,
        output_path: Path | str | None = None,
        **kwargs,
    ) -> 'ProcessDumper':
        """Creates a ProcessDumper instance configured from a YAML file.

        :param process: Identifier for the selected ``ProcessNode``.
        :param config_path: Path of the dump config file.
        :param output_path: Dump output path. If not given, same directory as where the config file is located.
        :return: ProcessDumper instance.
        """

        verified_process = cls._verify_process_node(process)
        config_path = Path(config_path).resolve()

        # Determine the final output path
        if output_path is None:
            resolved_path = Path(config_path).parent.resolve()
            logger.info(f'No output_path specified, using default: {resolved_path}')
        else:
            resolved_path = Path(output_path).resolve()

        # Prepare extra args for __init__
        init_extra_args = {'process': verified_process}

        # Delegate to the helper function
        return _create_dumper_instance(
            cls=cls,
            config_path=config_path,
            output_path=resolved_path,
            cls_init_extra_args=init_extra_args,
            **kwargs,
        )

    def __init__(
        self,
        process: orm.ProcessNode | int | str,
        config: DumpConfig | None = None,
        output_path: str | Path | None = None,
    ) -> None:
        """Initialize the ProcessDumper, which handles exporting a single AiiDA ProcessNode.

        :param process: The ``ProcessNode`` to dump, either given as ORM instance, or its PK or UUID.
        :param config: An optional ``DumpConfig`` object that controls what data to include in the dump.
            If ``None``, default dump settings are used.
        :param output_path: Optional base path to write the dump to. Can be a string or ``Path``.
            If ``None``, a default path based on the profile name will be used.
        """
        self.process_node = ProcessDumper._verify_process_node(process)
        self.config: DumpConfig = config if config is not None else DumpConfig()

        # Resolve DumpPaths based on output_path and the node
        if output_path is None:
            default_path = DumpPaths._get_default_process_dump_path(process_node=self.process_node)
            self.dump_paths = DumpPaths(parent=Path.cwd(), child=default_path)
        else:
            self.dump_paths = DumpPaths.from_path(Path(output_path).resolve())

    @staticmethod
    def _verify_process_node(
        identifier: orm.ProcessNode | int | str,
    ) -> orm.ProcessNode:
        """Verify that an identifier yields a valid ProcessNode instance.

        :raises NotExistent: If node not found for identifier.
        :raises TypeError: If loaded node is not a ProcessNode or input type is wrong.
        :raises ValueError: If another loading error occurs.
        """
        if isinstance(identifier, orm.ProcessNode):
            return identifier
        elif isinstance(identifier, (int, str)):
            try:
                loaded_node: orm.Node = orm.load_node(identifier=identifier)
            except NotExistent:
                logger.error(f"Process node with identifier '{identifier}' not found.")
                raise
            except Exception as exc:
                msg = f"Error loading process node via identifier '{identifier}': {exc}"
                raise ValueError(msg) from exc

            if not isinstance(loaded_node, orm.ProcessNode):
                msg = f'Node <{loaded_node.pk}> loaded, but it is not an orm.ProcessNode.'
                raise TypeError(msg)
            return loaded_node
        else:
            msg = f'Invalid type for process identifier: {type(identifier)}'
            raise TypeError(msg)

    def dump(self) -> None:
        """Perform the dump operation by invoking the engine."""
        # Instantiate engine for dump operation rather than on construction such that
        # Successive incremental dumps can be achieved with one instance
        engine = DumpEngine(config=self.config, dump_paths=self.dump_paths)
        engine.dump(entity=self.process_node)


class GroupDumper:
    """Dumps data in an AiiDA group."""

    @classmethod
    def from_config(
        cls,
        group: orm.Group | str | int,
        config_path: str | Path,
        output_path: Path | str | None = None,
        **kwargs,
    ) -> 'GroupDumper':
        """Creates a GroupDumper instance configured from a YAML file.

        :param process: Identifier for the selected ``Group``.
        :param config_path: Path of the dump config file.
        :param output_path: Dump output path. If not given, same directory as where the config file is located.
        :return: GroupDumper instance.
        """
        verified_group = cls._verify_group(group)
        config_path = Path(config_path).resolve()

        # Determine the final output path
        if output_path is None:
            resolved_path = Path(config_path).parent.resolve()
            logger.info(f'No output_path specified, using default: {resolved_path}')
        else:
            resolved_path = Path(output_path).resolve()

        # Prepare extra args for __init__
        init_extra_args = {'group': verified_group}

        # Delegate to the helper function
        return _create_dumper_instance(
            cls=cls,
            config_path=config_path,
            output_path=resolved_path,
            cls_init_extra_args=init_extra_args,
            **kwargs,
        )

    def __init__(
        self,
        group: orm.Group | str,
        config: DumpConfig | None = None,
        output_path: str | Path | None = None,
    ) -> None:
        """Initialize the GroupDumper, which handles exporting the data in an AiiDA group.

        :param group: The Group to dump, either given as ORM instance, or its PK or UUID.
        :param config: An optional ``DumpConfig`` object that controls what data to include in the dump.
            If ``None``, default dump settings are used.
        :param output_path: Optional base path to write the dump to. Can be a string or ``Path``.
            If ``None``, a default path based on the group label name will be used.
        """

        self.group: orm.Group = GroupDumper._verify_group(group)
        self.config: DumpConfig = config if config is not None else DumpConfig()

        if output_path is None:
            default_path = DumpPaths._get_default_group_dump_path(self.group)
            self.dump_paths = DumpPaths(parent=Path.cwd(), child=default_path)
        else:
            self.dump_paths = DumpPaths.from_path(Path(output_path).resolve())

    @staticmethod
    def _verify_group(identifier: orm.Group | str | int) -> orm.Group:
        """Verify the input is a valid Group instance or load it.

        :raises NotExistent: If group not found for identifier.
        :raises TypeError: If input type is wrong.
        :raises ValueError: If another loading error occurs.
        """
        if isinstance(identifier, orm.Group):
            # If it's already a Group instance, just return it
            return identifier
        elif isinstance(identifier, (str, int)):
            try:
                return orm.load_group(identifier=identifier)
            except NotExistent:
                logger.error(f"Group with identifier '{identifier}' not found.")
                raise
            except Exception as exc:
                msg = f"Error loading group via identifier '{identifier}': {exc}"
                raise ValueError(msg) from exc
        else:
            msg = f'Invalid type for group identifier: {type(identifier)}'
            raise TypeError(msg)

    def dump(self):
        """Perform the dump operation. Simply delegate to the engine."""
        # Instantiate engine for dump operation rather than on construction such that
        # Successive incremental dumps can be achieved with one instance
        engine = DumpEngine(config=self.config, dump_paths=self.dump_paths)
        engine.dump(entity=self.group)


class ProfileDumper:
    """Dumps data from the currently loaded AiiDA profile."""

    @classmethod
    def from_config(
        cls,
        config_path: str | Path,
        output_path: Path | str | None = None,
        **kwargs,
    ) -> 'ProfileDumper':
        """Creates a ProfileDumper instance configured from a YAML file.

        :param config_path: Path of the dump config file.
        :param output_path: Dump output path. If not given, same directory as where the config file is located.
        :return: ProfileDumper instance.
        """
        config_path = Path(config_path).resolve()

        # Determine the final output path
        if output_path is None:
            resolved_path = Path(config_path).parent.resolve()
        else:
            resolved_path = Path(output_path).resolve()

        # No extra args needed for ProfileDumper.__init__
        init_extra_args = {}

        # Delegate to the helper function
        return _create_dumper_instance(
            cls=cls,
            config_path=config_path,
            output_path=resolved_path,
            cls_init_extra_args=init_extra_args,
            **kwargs,
        )

    def __init__(self, config: DumpConfig | None = None, output_path: str | Path | None = None) -> None:
        """Initialize the ProfileDumper, which handles exporting data from an AiiDA profile.

        :param profile: The AiiDA profile to dump. Can be a `Profile` object, a profile name as a string,
            or ``None`` to use the currently loaded profile.
        :param config: An optional ``DumpConfig`` object that controls what data to include in the dump.
            If ``None``, default dump settings are used.
        :param output_path: Optional base path to write the dump to. Can be a string or ``Path``.
            If ``None``, a default path based on the profile name will be used.
        """

        self.config: DumpConfig = config if config is not None else DumpConfig()

        if output_path is None:
            default_path = DumpPaths._get_default_profile_dump_path()
            self.dump_paths = DumpPaths(parent=Path.cwd(), child=default_path)
        else:
            self.dump_paths = DumpPaths.from_path(Path(output_path).resolve())

    def dump(self):
        """Perform the dump operation. This simply delegates to the engine."""
        # Instantiate engine for dump operation rather than on construction such that
        # Successive incremental dumps can be achieved with one instance
        engine = DumpEngine(config=self.config, dump_paths=self.dump_paths)
        engine.dump()


def _apply_kwargs_overrides(config: DumpConfig, **kwargs) -> DumpConfig:
    """Applies kwargs overrides to a Pydantic DumpConfig object."""
    if not kwargs:
        return config

    try:
        # Filter kwargs to only include valid field names for DumpConfig
        # Pydantic's model_fields gives valid field names
        valid_field_names = set(config.model_fields.keys())
        valid_kwargs = {k: v for k, v in kwargs.items() if k in valid_field_names}
        ignored_kwargs = {k: v for k, v in kwargs.items() if k not in valid_field_names}

        if ignored_kwargs:
            logger.warning(f'Ignoring unknown configuration kwargs: {list(ignored_kwargs.keys())}')

        if not valid_kwargs:
            return config

        # Use model_copy which handles validation on update
        final_config = config.model_copy(update=valid_kwargs)
        return final_config

    except Exception as e:
        msg = f'Error applying kwargs overrides: {e}. Returning original config.'
        logger.error(msg, exc_info=True)
        return config


def _create_dumper_instance(
    *,
    cls: Type[ProcessDumper | GroupDumper | ProfileDumper],
    config_path: str | Path,
    output_path: Path,
    cls_init_extra_args: Dict[str, Any],
    **kwargs,
) -> ProcessDumper | GroupDumper | ProfileDumper:
    """Internal helper to load config, apply overrides, create paths, and instantiate a dumper facade.

    :param cls: The ``Dumper`` class that should be instantiated.
    :param config_path: Path of the dump config file.
    :param output_path: Dump output path. If not given, same directory as where the config file is located.
    :param cls_init_extra_args: Additional process or group identifier.
    :return: Instantiated ``Dumper`` class.
    """
    # 1. Load config from file using Pydantic parsing
    try:
        loaded_config = DumpConfig.parse_yaml_file(config_path)
    except (FileNotFoundError, ValueError) as e:
        # Log details before re-raising for the specific facade context
        logger.error(f'Error loading config for {cls.__name__}: {e}.')
        raise

    # 2. Apply kwargs overrides to the loaded config
    final_config = _apply_kwargs_overrides(loaded_config, **kwargs)

    # 3. Instantiate and return the specific dumper facade class
    # Combine config, paths, and any extra args needed by the specific __init__
    init_args = {
        'config': final_config,
        'output_path': output_path,
        **cls_init_extra_args,  # Add process/group if provided
    }
    return cls(**init_args)
