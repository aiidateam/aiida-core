###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Regenerate the ``export_main_0002_simple.aiida`` reference archive.

Thin wrapper around :func:`tests.utils.archives.generate_archive_main_0002`,
which statically defines the dataset in code. Re-run whenever the head
schema changes::

    uv run python tests/static/export/migrate/create_main_0002_simple.py
"""

import contextlib
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from aiida.manage.configuration import create_profile, get_config, profile_context, reset_config
from aiida.manage.configuration.settings import DEFAULT_AIIDA_PATH_VARIABLE, AiiDAConfigDir
from tests.static import STATIC_DIR
from tests.utils.archives import generate_archive_main_0002


@contextlib.contextmanager
def temporary_profile():
    """Create, load and tear down a temporary config and profile (standalone use only).

    Test runs should use the ``aiida_config_factory``/``aiida_profile_factory``
    fixtures instead of this helper.
    """
    with tempfile.TemporaryDirectory(prefix='create_main_0002_simple') as tmpdir:
        dirpath_config = Path(tmpdir) / '.aiida'
        current_path_variable = os.environ.get(DEFAULT_AIIDA_PATH_VARIABLE)
        try:
            current_config = get_config()
        except Exception:
            current_config = None
        reset_config()
        os.environ[DEFAULT_AIIDA_PATH_VARIABLE] = str(dirpath_config)
        AiiDAConfigDir.set(dirpath_config)
        config = get_config(create=True)
        profile = create_profile(
            config,
            storage_backend='core.sqlite_dos',
            storage_config={'filepath': str(Path(tmpdir) / 'storage')},
            broker_backend=None,
            broker_config=None,
            name='create-main-0002-simple',
            email='test@localhost',
            is_test_profile=True,
        )
        config.set_default_profile(profile.name)
        config.store()
        try:
            with profile_context(profile, allow_switch=True):
                yield profile
        finally:
            reset_config()
            if current_config is not None:
                AiiDAConfigDir.set(Path(current_config.dirpath))
                get_config()
            if current_path_variable is None:
                os.environ.pop(DEFAULT_AIIDA_PATH_VARIABLE, None)
            else:
                os.environ[DEFAULT_AIIDA_PATH_VARIABLE] = current_path_variable


def main() -> None:
    """Generate the archive and report its content."""
    with temporary_profile():
        dest = generate_archive_main_0002(STATIC_DIR / 'export' / 'migrate')
    print(f'wrote reference archive to {dest}')


if __name__ == '__main__':
    main()
