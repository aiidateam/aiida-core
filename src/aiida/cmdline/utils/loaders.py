###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Helpers to resolve command line identifiers into ORM entities from within a command body.

Command parameters carry identifiers as plain strings so that parsing a ``verdi`` command line does not require a
storage backend. Resolving them is the responsibility of the command, which does so through the helpers in this module
once the backend has been loaded.

The parameter declaration stays the single source of truth: the helpers look up the parameter that supplied the
identifier and delegate to its ``resolve`` method, so restrictions such as ``sub_classes`` are declared once on the
parameter rather than repeated in every command body.
"""

from __future__ import annotations

import typing as t

import click

if t.TYPE_CHECKING:
    from aiida.orm import Computer, Group, Node, User

__all__ = (
    'load_calculation',
    'load_calculations',
    'load_code',
    'load_codes',
    'load_computer',
    'load_computers',
    'load_data',
    'load_datum',
    'load_entities',
    'load_entity',
    'load_group',
    'load_groups',
    'load_node',
    'load_nodes',
    'load_process',
    'load_processes',
    'load_user',
    'resolve_callback',
)


class _Resolvable(t.Protocol):
    """A click parameter type that can resolve an identifier into an ORM entity."""

    def resolve(self, identifier: str) -> t.Any: ...


def _find_param(param_name: str) -> click.Parameter | None:
    """Return the parameter of the command currently being invoked, if it can be determined."""
    context = click.get_current_context(silent=True)

    if context is None:
        return None

    return next((each for each in context.command.params if each.name == param_name), None)


def _resolvable_type(param: click.Parameter | None) -> _Resolvable | None:
    """Return the type of the parameter that resolves identifiers, unwrapping multi-value parameters."""
    from aiida.cmdline.params.types.multiple import MultipleValueParamType

    if param is None:
        return None

    param_type = param.type

    if isinstance(param_type, MultipleValueParamType):
        param_type = param_type.param_type

    return t.cast('_Resolvable', param_type) if hasattr(param_type, 'resolve') else None


def load_entity(identifier: str, *, param_name: str) -> t.Any:
    """Return the ORM entity that the identifier maps onto.

    The parameter named ``param_name`` supplies the type that performs the lookup, so any restriction declared on it
    is applied here.

    :param identifier: PK, UUID or label of the entity, as given on the command line.
    :param param_name: Name of the command parameter that supplied the identifier.
    :raises click.BadParameter: if the identifier is ambiguous or maps onto no entity.
    :raises RuntimeError: if ``param_name`` does not name a parameter that can resolve identifiers.
    """
    from aiida.common import exceptions

    param = _find_param(param_name)
    param_type = _resolvable_type(param)

    if param_type is None:
        msg = f'parameter `{param_name}` does not declare a type that can resolve identifiers'
        raise RuntimeError(msg)

    try:
        return param_type.resolve(identifier)
    except (exceptions.MultipleObjectsError, exceptions.NotExistent, ValueError) as exception:
        raise click.BadParameter(str(exception), ctx=click.get_current_context(silent=True), param=param) from exception


def resolve_callback(ctx: click.Context, param: click.Parameter, value: t.Any) -> t.Any:
    """Click callback that resolves an identifier while the command line is still being parsed.

    Command bodies should call :func:`load_entity` instead. Use this only for parameters whose loaded entity is needed
    during parsing itself, such as when a later parameter derives its interactive default or its validation from it.
    Because it runs before the command body, it loads the storage backend itself.
    """
    from aiida.cmdline.utils.decorators import load_backend_if_not_loaded

    if value is None:
        return None

    load_backend_if_not_loaded()
    return load_entity(value, param_name=t.cast(str, param.name))


def load_entities(identifiers: t.Sequence[str], *, param_name: str) -> list[t.Any]:
    """Return the ORM entities that the identifiers map onto.

    All identifiers are resolved before returning, so a command never acts on a partially resolved selection.

    :param identifiers: PKs, UUIDs or labels of the entities, as given on the command line.
    :param param_name: Name of the command parameter that supplied the identifiers.
    :raises click.BadParameter: if an identifier is ambiguous or maps onto no entity.
    """
    return [load_entity(identifier, param_name=param_name) for identifier in identifiers]


def load_node(identifier: str, *, param_name: str = 'node') -> Node:
    """Return the node that the identifier maps onto. See :func:`load_entity`."""
    return t.cast('Node', load_entity(identifier, param_name=param_name))


def load_nodes(identifiers: t.Sequence[str], *, param_name: str = 'nodes') -> list[Node]:
    """Return the nodes that the identifiers map onto. See :func:`load_entities`."""
    return t.cast('list[Node]', load_entities(identifiers, param_name=param_name))


def load_group(identifier: str, *, param_name: str = 'group') -> Group:
    """Return the group that the identifier maps onto. See :func:`load_entity`."""
    return t.cast('Group', load_entity(identifier, param_name=param_name))


def load_groups(identifiers: t.Sequence[str], *, param_name: str = 'groups') -> list[Group]:
    """Return the groups that the identifiers map onto. See :func:`load_entities`."""
    return t.cast('list[Group]', load_entities(identifiers, param_name=param_name))


def load_computer(identifier: str, *, param_name: str = 'computer') -> Computer:
    """Return the computer that the identifier maps onto. See :func:`load_entity`."""
    return t.cast('Computer', load_entity(identifier, param_name=param_name))


def load_computers(identifiers: t.Sequence[str], *, param_name: str = 'computers') -> list[Computer]:
    """Return the computers that the identifiers map onto. See :func:`load_entities`."""
    return t.cast('list[Computer]', load_entities(identifiers, param_name=param_name))


def load_user(identifier: str, *, param_name: str = 'user') -> User:
    """Return the user with the given email address. See :func:`load_entity`."""
    return t.cast('User', load_entity(identifier, param_name=param_name))


def load_code(identifier: str, *, param_name: str = 'code') -> t.Any:
    """Return the code that the identifier maps onto. See :func:`load_entity`."""
    return load_entity(identifier, param_name=param_name)


def load_codes(identifiers: t.Sequence[str], *, param_name: str = 'codes') -> list[t.Any]:
    """Return the codes that the identifiers map onto. See :func:`load_entities`."""
    return load_entities(identifiers, param_name=param_name)


def load_process(identifier: str, *, param_name: str = 'process') -> t.Any:
    """Return the process node that the identifier maps onto. See :func:`load_entity`."""
    return load_entity(identifier, param_name=param_name)


def load_processes(identifiers: t.Sequence[str], *, param_name: str = 'processes') -> list[t.Any]:
    """Return the process nodes that the identifiers map onto. See :func:`load_entities`."""
    return load_entities(identifiers, param_name=param_name)


def load_calculation(identifier: str, *, param_name: str = 'calculation') -> t.Any:
    """Return the calculation node that the identifier maps onto. See :func:`load_entity`."""
    return load_entity(identifier, param_name=param_name)


def load_calculations(identifiers: t.Sequence[str], *, param_name: str = 'calculations') -> list[t.Any]:
    """Return the calculation nodes that the identifiers map onto. See :func:`load_entities`."""
    return load_entities(identifiers, param_name=param_name)


def load_datum(identifier: str, *, param_name: str = 'datum') -> t.Any:
    """Return the data node that the identifier maps onto. See :func:`load_entity`."""
    return load_entity(identifier, param_name=param_name)


def load_data(identifiers: t.Sequence[str], *, param_name: str = 'data') -> list[t.Any]:
    """Return the data nodes that the identifiers map onto. See :func:`load_entities`."""
    return load_entities(identifiers, param_name=param_name)
