###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
###########################################################################
"""Shared Alembic migration driver."""

from __future__ import annotations

import contextlib
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from alembic.command import downgrade, stamp, upgrade
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext, MigrationInfo
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, MetaData

from aiida.storage.log import MIGRATE_LOGGER

if TYPE_CHECKING:
    from aiida.manage.configuration.profile import Profile


class AlembicMigrator:
    """Alembic driver for one migration script directory.

    The driver owns no database resources. Callers supply an open connection,
    allowing profile storage backends and archive migrations to use it alike.
    """

    def __init__(self, script_location: Path, target_metadata: Callable[[], MetaData]) -> None:
        self._script_location = script_location
        self._target_metadata = target_metadata

    def _alembic_config(self) -> Config:
        """Return an Alembic configuration for the migration directory."""
        config = Config()
        config.set_main_option('script_location', str(self._script_location))
        return config

    def _alembic_script(self) -> ScriptDirectory:
        """Return the Alembic script directory."""
        return ScriptDirectory.from_config(self._alembic_config())

    def get_schema_versions(self) -> dict[str, str]:
        """Return all Alembic schema versions, from oldest to latest."""
        return {entry.revision: entry.doc for entry in reversed(list(self._alembic_script().walk_revisions()))}

    def get_schema_version_head(self) -> str:
        """Return the head of the ``main`` migration branch."""
        return self._alembic_script().revision_map.get_current_head('main') or ''

    @contextlib.contextmanager
    def _alembic_connect(self, connection: Connection, *, profile: Profile | None = None) -> Iterator[Config]:
        """Configure Alembic to use an existing connection."""
        config = self._alembic_config()
        config.attributes['connection'] = connection
        config.attributes['aiida_profile'] = profile
        config.attributes['target_metadata'] = self._target_metadata()

        def callback(step: MigrationInfo, **kwargs: Any) -> None:
            from_revision = step.down_revision_ids[0] if step.down_revision_ids else '<base>'
            MIGRATE_LOGGER.report(f'- {from_revision} -> {step.up_revision_id}')

        config.attributes['on_version_apply'] = callback
        yield config

    @contextlib.contextmanager
    def migration_context(
        self, connection: Connection, *, profile: Profile | None = None
    ) -> Iterator[MigrationContext]:
        """Return a migration context configured for an existing connection."""
        with self._alembic_connect(connection, profile=profile) as config:
            script = ScriptDirectory.from_config(config)
            with EnvironmentContext(config, script) as environment:
                environment.configure(connection)
                yield environment.get_context()

    def migrate_up(self, connection: Connection, version: str, *, profile: Profile | None = None) -> None:
        """Upgrade an existing connection to ``version``."""
        with self._alembic_connect(connection, profile=profile) as config:
            upgrade(config, version)

    def migrate_down(self, connection: Connection, version: str, *, profile: Profile | None = None) -> None:
        """Downgrade an existing connection to ``version``."""
        with self._alembic_connect(connection, profile=profile) as config:
            downgrade(config, version)

    def stamp(self, connection: Connection, version: str, *, profile: Profile | None = None) -> None:
        """Stamp an existing connection with ``version`` without running migrations."""
        with self._alembic_connect(connection, profile=profile) as config:
            stamp(config, version)
