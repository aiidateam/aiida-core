# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Click parameter type for AiiDA Plugins."""
import functools

import click
from importlib_metadata import EntryPoint

from aiida.common import exceptions
from aiida.plugins import factories
from aiida.plugins.entry_point import (
    ENTRY_POINT_GROUP_PREFIX,
    ENTRY_POINT_STRING_SEPARATOR,
    EntryPointFormat,
    format_entry_point_string,
    get_entry_point,
    get_entry_point_groups,
    get_entry_point_string_format,
    get_entry_points,
)

from .strings import EntryPointType

__all__ = ('PluginParamType',)


class PluginParamType(EntryPointType):
    """
    AiiDA Plugin name parameter type.

    :param group: string or tuple of strings, where each is a valid entry point group. Adding the `aiida.`
        prefix is optional. If it is not detected it will be prepended internally.
    :param load: when set to True, convert will not return the entry point, but the loaded entry point

    Usage::

        click.option(... type=PluginParamType(group='aiida.calculations')

    or::

        click.option(... type=PluginParamType(group=('calculations', 'data'))

    """
    name = 'plugin'

    _factory_mapping = {
        'aiida.calculations': factories.CalculationFactory,
        'aiida.data': factories.DataFactory,
        'aiida.groups': factories.GroupFactory,
        'aiida.parsers': factories.ParserFactory,
        'aiida.schedulers': factories.SchedulerFactory,
        'aiida.transports': factories.TransportFactory,
        'aiida.tools.dbimporters': factories.DbImporterFactory,
        'aiida.tools.data.orbitals': factories.OrbitalFactory,
        'aiida.workflows': factories.WorkflowFactory,
    }

    def __init__(self, group=None, load=False, *args, **kwargs):
        """
        Validate that group is either a string or a tuple of valid entry point groups, or if it
        is not specified use the tuple of all recognized entry point groups.
        """
        # pylint: disable=keyword-arg-before-vararg
        valid_entry_point_groups = get_entry_point_groups()

        if group is None:
            self._groups = tuple(valid_entry_point_groups)
        else:
            if isinstance(group, str):
                invalidated_groups = tuple([group])
            elif isinstance(group, tuple):
                invalidated_groups = group
            else:
                raise ValueError('invalid type for group')

            groups = []

            for grp in invalidated_groups:

                if not grp.startswith(ENTRY_POINT_GROUP_PREFIX):
                    grp = ENTRY_POINT_GROUP_PREFIX + grp

                if grp not in valid_entry_point_groups:
                    raise ValueError(f'entry point group {grp} is not recognized')

                groups.append(grp)

            self._groups = tuple(groups)

        self._init_entry_points()
        self.load = load

        super().__init__(*args, **kwargs)

    def _init_entry_points(self):
        """
        Populate entry point information that will be used later on.  This should only be called
        once in the constructor after setting self.groups because the groups should not be changed
        after instantiation
        """
        self._entry_points = [(group, entry_point) for group in self.groups for entry_point in get_entry_points(group)]
        self._entry_point_names = [entry_point.name for group in self.groups for entry_point in get_entry_points(group)]

    @property
    def groups(self):
        return self._groups

    @property
    def has_potential_ambiguity(self):
        """
        Returns whether the set of supported entry point groups can lead to ambiguity when only an entry point name
        is specified. This will happen if one ore more groups share an entry point with a common name
        """
        return len(self._entry_point_names) != len(set(self._entry_point_names))

    def get_valid_arguments(self):
        """
        Return a list of all available plugins for the groups configured for this PluginParamType instance.
        If the entry point names are not unique, because there are multiple groups that contain an entry
        point that has an identical name, we need to prefix the names with the full group name

        :returns: list of valid entry point strings
        """
        if self.has_potential_ambiguity:
            fmt = EntryPointFormat.FULL
            return sorted([format_entry_point_string(group, ep.name, fmt=fmt) for group, ep in self._entry_points])

        return sorted(self._entry_point_names)

    def get_possibilities(self, incomplete=''):
        """
        Return a list of plugins starting with incomplete
        """
        if incomplete == '':
            return self.get_valid_arguments()

        # If there is a chance of ambiguity we always return the entry point string in FULL format, otherwise
        # return the possibilities in the same format as the incomplete. Note that this may have some unexpected
        # effects. For example if incomplete equals `aiida.` or `calculations` it will be detected as the MINIMAL
        # format, even though they would also be the valid beginnings of a FULL or PARTIAL format, except that we
        # cannot know that for sure at this time
        if self.has_potential_ambiguity:
            possibilites = [eps for eps in self.get_valid_arguments() if eps.startswith(incomplete)]
        else:
            possibilites = []
            fmt = get_entry_point_string_format(incomplete)

            for group, entry_point in self._entry_points:
                entry_point_string = format_entry_point_string(group, entry_point.name, fmt=fmt)
                if entry_point_string.startswith(incomplete):
                    possibilites.append(entry_point_string)

        return possibilites

    def shell_complete(self, ctx, param, incomplete):  # pylint: disable=unused-argument
        """
        Return possible completions based on an incomplete value

        :returns: list of tuples of valid entry points (matching incomplete) and a description
        """
        return [click.shell_completion.CompletionItem(p) for p in self.get_possibilities(incomplete=incomplete)]

    def get_missing_message(self, param):  # pylint: disable=unused-argument
        return 'Possible arguments are:\n\n' + '\n'.join(self.get_valid_arguments())

    def get_entry_point_from_string(self, entry_point_string):
        """
        Validate a given entry point string, which means that it should have a valid entry point string format
        and that the entry point unambiguously corresponds to an entry point in the groups configured for this
        instance of PluginParameterType.

        :returns: the entry point if valid
        :raises: ValueError if the entry point string is invalid
        """
        group = None
        name = None

        entry_point_format = get_entry_point_string_format(entry_point_string)

        if entry_point_format in (EntryPointFormat.FULL, EntryPointFormat.PARTIAL):

            group, name = entry_point_string.split(ENTRY_POINT_STRING_SEPARATOR)

            if entry_point_format == EntryPointFormat.PARTIAL:
                group = ENTRY_POINT_GROUP_PREFIX + group

            self.validate_entry_point_group(group)

        elif entry_point_format == EntryPointFormat.MINIMAL:

            name = entry_point_string
            matching_groups = {group for group, entry_point in self._entry_points if entry_point.name == name}

            if len(matching_groups) > 1:
                raise ValueError(
                    "entry point '{}' matches more than one valid entry point group [{}], "
                    'please specify an explicit group prefix: {}'.format(
                        name, ' '.join(matching_groups), self._entry_points
                    )
                )
            elif not matching_groups:
                raise ValueError(
                    "entry point '{}' is not valid for any of the allowed "
                    'entry point groups: {}'.format(name, ' '.join(self.groups))
                )

            group = matching_groups.pop()

        else:
            ValueError(f'invalid entry point string format: {entry_point_string}')

        # If there is a factory for the entry point group, use that, otherwise use ``get_entry_point``
        try:
            get_entry_point_partial = functools.partial(self._factory_mapping[group], load=False)
        except KeyError:
            get_entry_point_partial = functools.partial(get_entry_point, group)

        try:
            return get_entry_point_partial(name)
        except exceptions.EntryPointError as exception:
            raise ValueError(exception)

    def validate_entry_point_group(self, group):
        if group not in self.groups:
            raise ValueError(f'entry point group `{group}` is not supported by this parameter.')

    def convert(self, value, param, ctx):
        """
        Convert the string value to an entry point instance, if the value can be successfully parsed
        into an actual entry point. Will raise click.BadParameter if validation fails.
        """
        # If the value is already of the expected return type, simply return it. This behavior is new in `click==8.0`:
        # https://click.palletsprojects.com/en/8.0.x/parameters/#implementing-custom-types
        if isinstance(value, EntryPoint):
            try:
                self.validate_entry_point_group(value.group)
            except ValueError as exception:
                raise click.BadParameter(str(exception))
            return value

        value = super().convert(value, param, ctx)

        try:
            entry_point = self.get_entry_point_from_string(value)
            self.validate_entry_point_group(entry_point.group)
        except ValueError as exception:
            raise click.BadParameter(str(exception))

        if self.load:
            try:
                return entry_point.load()
            except exceptions.LoadingEntryPointError as exception:
                raise click.BadParameter(str(exception))
        else:
            return entry_point
