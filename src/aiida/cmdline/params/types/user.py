###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""User param type for click."""

from __future__ import annotations

import typing as t

import click
from click.shell_completion import CompletionItem

from aiida.cmdline.utils.decorators import with_dbenv

if t.TYPE_CHECKING:
    from aiida import orm

__all__ = ('UserParamType',)


class UserParamType(click.ParamType):
    """The user parameter type for click.   Can get or create a user."""

    name = 'user'

    def __init__(self, create: bool = False):
        """:param create: If the user does not exist, create a new instance (unstored)."""
        self._create = create

    def convert(self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None) -> str:
        """Validate the email and return it unchanged.

        Looking the user up requires a storage backend, which parsing a command line must not need. Commands resolve
        the email in their body through :mod:`aiida.cmdline.utils.loaders`, which calls :meth:`resolve`.
        """
        return t.cast(str, super().convert(value, param, ctx))

    def resolve(self, identifier: str) -> orm.User:
        """Return the user with the given email address.

        :param identifier: email address of the user.
        :raises aiida.common.NotExistent: if no user has this email and the parameter does not create one.
        :raises aiida.common.MultipleObjectsError: if more than one user has this email.
        """
        from aiida import orm
        from aiida.common import exceptions

        results = orm.User.collection.find({'email': identifier})

        if not results:
            if self._create:
                return orm.User(email=identifier)

            raise exceptions.NotExistent(f"User '{identifier}' not found")

        if len(results) > 1:
            raise exceptions.MultipleObjectsError(f"Multiple users found with email '{identifier}': {results}")

        return results[0]

    @with_dbenv()
    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:
        """Return possible completions based on an incomplete value

        :returns: list of tuples of valid entry points (matching incomplete) and a description
        """
        from aiida import orm

        users = orm.User.collection.find()

        return [CompletionItem(user.email) for user in users if user.email.startswith(incomplete)]
