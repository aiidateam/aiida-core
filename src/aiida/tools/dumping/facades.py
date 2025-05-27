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

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.common.warnings import warn_deprecation
from aiida.tools.dumping.config import DumpConfig
from aiida.tools.dumping.engine import DumpEngine
from aiida.tools.dumping.utils import DumpPaths

logger = AIIDA_LOGGER.getChild('tools.dumping.facades')


class ProcessDumper:
    """Dumps data of a single ProcessNode."""

    def __init__(
        self,
        process_node: orm.ProcessNode,
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

        self.process_node = process_node
        self.config: DumpConfig = config if config is not None else DumpConfig()
        self.base_output_path: Path

        # Resolve DumpPaths based on output_path and the node
        if not output_path:
            default_child_dir_name = str(DumpPaths.get_default_dump_path(self.process_node))
            self.base_output_path = Path.cwd() / default_child_dir_name
        else:
            self.base_output_path = Path(output_path).resolve()

    def dump(self) -> None:
        """Perform the dump operation by invoking the engine."""
        # Instantiate engine for dump operation rather than on construction such that
        # Successive incremental dumps can be achieved with one instance
        warn_deprecation(
            'The `ProcessDumper` class is deprecated. Use `orm.ProcessNode.dump()` instead.',
            version=3,
        )
        engine = DumpEngine(
            base_output_path=self.base_output_path,
            config=self.config,
            dump_target_entity=self.process_node,
        )
        engine.dump()
