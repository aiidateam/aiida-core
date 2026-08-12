###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Profile param type for click."""

from __future__ import annotations

import typing as t

import click
from click.shell_completion import CompletionItem

from .strings import LabelStringType

if t.TYPE_CHECKING:
    from aiida.manage.configuration import Profile

__all__ = ('ProfileParamType',)


class ProfileParamType(LabelStringType):
    """The profile parameter type for click.

    This parameter type requires the command that uses it to define the ``context_class`` class attribute to be the
    :class:`aiida.cmdline.groups.verdi.VerdiContext` class, as that is responsible for creating the user defined object
    ``obj`` on the context and loads the instance config.
    """

    name = 'profile'

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        self._cannot_exist = kwargs.pop('cannot_exist', False)
        self._load_profile = kwargs.pop('load_profile', False)  # If True, will load the profile converted from value
        # If True, a value that looks like an archive location (``http(s)://`` URL or ``file://`` path) is converted
        # to an ephemeral archive profile, instead of being interpreted as the name of a configured profile.
        self._accept_archive_location = kwargs.pop('accept_archive_location', False)
        super().__init__(*args, **kwargs)

    @staticmethod
    def deconvert_default(value: t.Any) -> t.Any:
        return value.name

    def convert(self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None) -> Profile:  # type: ignore[override]
        """Attempt to match the given value to a valid profile."""
        from aiida.common.exceptions import MissingConfigurationError, ProfileConfigurationError
        from aiida.manage.configuration import Profile, load_profile

        try:
            config = ctx.obj.config  # type: ignore[union-attr]
        except AttributeError:
            raise RuntimeError(
                'The context does not contain a user defined object with the loaded AiiDA configuration. '
                'Is your click command setting `context_class` to :class:`aiida.cmdline.groups.verdi.VerdiContext`?'
            )

        # If the value is already of the expected return type, simply return it. This behavior is new in `click==8.0`:
        # https://click.palletsprojects.com/en/8.0.x/parameters/#implementing-custom-types
        if isinstance(value, Profile):
            return value

        if (
            self._accept_archive_location
            and not self._cannot_exist
            and isinstance(value, str)
            and value.lower().startswith(('http://', 'https://', 'file://'))
        ):
            profile = self._convert_archive_location(value, param, ctx)
        else:
            value = super().convert(value, param, ctx)

            try:
                profile = config.get_profile(value)
            except (MissingConfigurationError, ProfileConfigurationError) as exception:
                if not self._cannot_exist:
                    self.fail(str(exception))

                # Create a new empty profile
                profile = Profile(value, {}, validate=False)
            else:
                if self._cannot_exist:
                    self.fail(str(f'the profile `{value}` already exists'))

        profile = self._apply_cache_flags(profile, ctx)

        if self._load_profile:
            load_profile(profile)

        ctx.obj.profile = profile  # type: ignore[union-attr]

        return profile

    @staticmethod
    def _apply_cache_flags(profile: Profile, ctx: click.Context | None) -> Profile:
        """Record the ``--use-cache``/``--force-cache`` flags from the context in the profile, if they were set.

        For profiles using the ``core.sqlite_zip`` storage backend, the flags are recorded in the storage
        configuration of a detached copy of the profile, such that they are never persisted to the configuration
        file. For other storage backends the flags do not apply and are ignored with a warning.
        """
        import copy

        from aiida.manage.configuration import Profile

        use_cache = getattr(ctx.obj, 'use_cache', False) if ctx else False
        force_cache = getattr(ctx.obj, 'force_cache', False) if ctx else False

        if not (use_cache or force_cache):
            return profile

        try:
            storage_backend = profile.storage_backend
        except KeyError:
            return profile

        if storage_backend != 'core.sqlite_zip':
            from aiida.cmdline.utils import echo

            names = [name for name, passed in (('--use-cache', use_cache), ('--force-cache', force_cache)) if passed]
            flags = ' and '.join(f'`{name}`' for name in names)
            echo.echo_warning(
                f'The {flags} option{"s" if len(names) > 1 else ""} only appl{"y" if len(names) > 1 else "ies"} to '
                f'profiles using the `core.sqlite_zip` storage backend, but profile `{profile.name}` uses '
                f'`{storage_backend}`: ignoring.'
            )
            return profile

        profile = Profile(profile.name, copy.deepcopy(profile.dictionary))

        if use_cache:
            profile.storage_config['use_cache'] = True
        if force_cache:
            profile.storage_config['force_cache'] = True

        return profile

    def _convert_archive_location(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> Profile:
        """Create an ephemeral profile mounting the ``.aiida`` archive at the given location as its storage.

        The profile uses the read-only ``core.sqlite_zip`` storage backend and is not added to the configuration
        file, so it only lives for the duration of the current interpreter.

        :param value: the location of the archive: an ``http(s)://`` URL of a remote archive, or a ``file://`` URL
            of a local one. The latter must be of the form ``file:///absolute/path`` (an empty or ``localhost`` host
            is accepted); percent-encoded characters in the path are decoded.
        """
        from pathlib import Path
        from urllib.parse import urlsplit

        from aiida.common.utils import url2pathname
        from aiida.storage.sqlite_zip.backend import SqliteZipBackend

        filepath: str | Path = value

        if value.lower().startswith('file://'):
            parts = urlsplit(value)
            if parts.netloc not in ('', 'localhost'):
                self.fail(
                    f'unsupported host `{parts.netloc}` in the file URL `{value}`: '
                    'use the form `file:///absolute/path`.',
                    param,
                    ctx,
                )
            filepath = Path(url2pathname(parts.path))
            if not filepath.is_file():
                self.fail(f'the archive `{filepath}` does not exist.', param, ctx)

        return SqliteZipBackend.create_profile(filepath)

    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:
        """Return possible completions based on an incomplete value

        :returns: list of tuples of valid entry points (matching incomplete) and a description
        """
        from aiida.common.exceptions import MissingConfigurationError
        from aiida.manage.configuration import get_config

        if self._cannot_exist:
            return []

        try:
            config = get_config()
        except MissingConfigurationError:
            return []

        return [CompletionItem(profile.name) for profile in config.profiles if profile.name.startswith(incomplete)]
