# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to manage the autogrouping functionality by ``verdi run``."""
import re
from typing import List, Optional

from aiida.common import exceptions, timezone
from aiida.common.escaping import escape_for_sql_like, get_regex_pattern_from_sql
from aiida.orm import AutoGroup, QueryBuilder
from aiida.plugins.entry_point import get_entry_point_string_from_class


class AutogroupManager:
    """Class to automatically add all newly stored ``Node``s to an ``AutoGroup`` (whilst enabled).

    This class should not be instantiated directly, but rather accessed through the backend storage instance.

    The auto-grouping is checked by the ``Node.store()`` method which, if ``is_to_be_grouped`` is true,
    will store the node in the associated ``AutoGroup``.

    The exclude/include lists are lists of strings like:
    ``aiida.data:core.int``, ``aiida.calculation:quantumespresso.pw``,
    ``aiida.data:core.array.%``, ...
    i.e.: a string identifying the base class, followed by a colon and the path to the class
    as accepted by CalculationFactory/DataFactory.
    Each string can contain one or more wildcard characters ``%``;
    in this case this is used in a ``like`` comparison with the QueryBuilder.
    Note that in this case you have to remember that ``_`` means "any character"
    in the QueryBuilder, and you need to escape it if you mean a literal underscore.

    Only one of the two (between exclude and include) can be set.
    If none of the two is set, everything is included.
    """

    def __init__(self, backend):
        """Initialize the manager for the storage backend."""
        self._backend = backend

        self._enabled = False
        self._exclude: Optional[List[str]] = None
        self._include: Optional[List[str]] = None

        self._group_label_prefix = f"Verdi autogroup on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self._group_label = None  # Actual group label, set by `get_or_create_group`

    @property
    def is_enabled(self) -> bool:
        """Return whether auto-grouping is enabled."""
        return self._enabled

    def enable(self) -> None:
        """Enable the auto-grouping."""
        self._enabled = True

    def disable(self) -> None:
        """Disable the auto-grouping."""
        self._enabled = False

    def get_exclude(self) -> Optional[List[str]]:
        """Return the list of classes to exclude from autogrouping.

        Returns ``None`` if no exclusion list has been set."""
        return self._exclude

    def get_include(self) -> Optional[List[str]]:
        """Return the list of classes to include in the autogrouping.

        Returns ``None`` if no inclusion list has been set."""
        return self._include

    def get_group_label_prefix(self) -> str:
        """Get the prefix of the label of the group.
        If no group label prefix was set, it will set a default one by itself."""
        return self._group_label_prefix

    @staticmethod
    def validate(strings: Optional[List[str]]):
        """Validate the list of strings passed to set_include and set_exclude."""
        if strings is None:
            return
        valid_prefixes = set(['aiida.node', 'aiida.calculations', 'aiida.workflows', 'aiida.data'])
        for string in strings:
            pieces = string.split(':')
            if len(pieces) != 2:
                raise exceptions.ValidationError(
                    f"'{string}' is not a valid include/exclude filter, must contain two parts split by a colon"
                )
            if pieces[0] not in valid_prefixes:
                raise exceptions.ValidationError(
                    f"'{string}' has an invalid prefix, must be among: {sorted(valid_prefixes)}"
                )

    def set_exclude(self, exclude: Optional[List[str]]) -> None:
        """Set the list of classes to exclude in the autogrouping.

        :param exclude: a list of valid entry point strings (might contain '%' to be used as
          string to be matched using SQL's ``LIKE`` pattern-making logic), or ``None``
          to specify no include list.
        """
        if isinstance(exclude, str):
            exclude = [exclude]
        self.validate(exclude)
        if exclude is not None and self.get_include() is not None:
            # It's ok to set None, both as a default, or to 'undo' the exclude list
            raise exceptions.ValidationError('Cannot both specify exclude and include')
        self._exclude = exclude

    def set_include(self, include: Optional[List[str]]) -> None:
        """Set the list of classes to include in the autogrouping.

        :param include: a list of valid entry point strings (might contain '%' to be used as
          string to be matched using SQL's ``LIKE`` pattern-making logic), or ``None``
          to specify no include list.
        """
        if isinstance(include, str):
            include = [include]
        self.validate(include)
        if include is not None and self.get_exclude() is not None:
            # It's ok to set None, both as a default, or to 'undo' the include list
            raise exceptions.ValidationError('Cannot both specify exclude and include')
        self._include = include

    def set_group_label_prefix(self, label_prefix: Optional[str]) -> None:
        """Set the label of the group to be created (or use a default)."""
        if label_prefix is None:
            label_prefix = f"Verdi autogroup on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if not isinstance(label_prefix, str):
            raise exceptions.ValidationError('group label must be a string')
        self._group_label_prefix = label_prefix
        self._group_label = None  # reset the actual group label

    @staticmethod
    def _matches(string, filter_string):
        """Check if 'string' matches the 'filter_string' (used for include and exclude filters).

        If 'filter_string' does not contain any % sign, perform an exact match.
        Otherwise, match with a SQL-like query, where % means any character sequence,
        and _ means a single character (these characters can be escaped with a backslash).

        :param string: the string to match.
        :param filter_string: the filter string.
        """
        if '%' in filter_string:
            regex_filter = get_regex_pattern_from_sql(filter_string)
            return re.match(regex_filter, string) is not None
        return string == filter_string

    def is_to_be_grouped(self, node) -> bool:
        """Return whether the given node is to be auto-grouped according to enable state and include/exclude lists."""
        if not self._enabled:
            return False
        # strings, including possibly 'all'
        include = self.get_include()
        exclude = self.get_exclude()
        if include is None and exclude is None:
            # Include all classes by default if nothing is explicitly specified.
            return True

        # We should never be here, anyway - this should be catched by the `set_include/exclude` methods
        assert include is None or exclude is None, "You cannot specify both an 'include' and an 'exclude' list"

        entry_point_string = node.process_type
        # If there is no `process_type` we are dealing with a `Data` node so we get the entry point from the class
        if not entry_point_string:
            entry_point_string = get_entry_point_string_from_class(node.__class__.__module__, node.__class__.__name__)
        if include is not None:
            # As soon as a filter string matches, we include the class
            return any(self._matches(entry_point_string, filter_string) for filter_string in include)
        # If we are here, exclude is not None
        # include *only* in *none* of the filters match (that is, exclude as
        # soon as any of the filters matches)
        return not any(self._matches(entry_point_string, filter_string) for filter_string in (exclude or []))

    def get_or_create_group(self) -> AutoGroup:
        """Return the current `AutoGroup`, or create one if None has been set yet.

        This function implements a somewhat complex logic that is however needed
        to make sure that, even if `verdi run` is called at the same time multiple
        times, e.g. in a for loop in bash, there is never the risk that two ``verdi run``
        Unix processes try to create the same group, with the same label, ending
        up in a crash of the code (see PR #3650).

        Here, instead, we make sure that if this concurrency issue happens,
        one of the two will get a IntegrityError from the DB, and then recover
        trying to create a group with a different label (with a numeric suffix appended),
        until it manages to create it.
        """
        # When this function is called, if it is the first time, just generate
        # a new group name (later on, after this ``if`` block`).
        # In that case, we will later cache in ``self._group_label`` the group label,
        # So the group with the same name can be returned quickly in future
        # calls of this method.
        if self._group_label is not None:
            builder = QueryBuilder(backend=self._backend).append(AutoGroup, filters={'label': self._group_label})
            results = [res[0] for res in builder.iterall()]
            if results:
                # If it is not empty, it should have only one result due to the uniqueness constraints
                assert len(results) == 1, 'I got more than one autogroup with the same label!'
                return results[0]
            # There are no results: probably the group has been deleted.
            # I continue as if it was not cached
            self._group_label = None

        label_prefix = self.get_group_label_prefix()
        # Try to do a preliminary QB query to avoid to do too many try/except
        # if many of the prefix_NUMBER groups already exist
        queryb = QueryBuilder(self._backend).append(
            AutoGroup,
            filters={
                'or': [{
                    'label': {
                        '==': label_prefix
                    }
                }, {
                    'label': {
                        'like': f"{escape_for_sql_like(f'{label_prefix}_')}%"
                    }
                }]
            },
            project='label'
        )
        existing_group_labels = [res[0][len(label_prefix):] for res in queryb.all()]
        existing_group_ints = []
        for label in existing_group_labels:
            if label == '':
                # This is just the prefix without name - corresponds to counter = 0
                existing_group_ints.append(0)
            elif label.startswith('_'):
                try:
                    existing_group_ints.append(int(label[1:]))
                except ValueError:
                    # It's not an integer, so it will never collide - just ignore it
                    pass

        if not existing_group_ints:
            counter = 0
        else:
            counter = max(existing_group_ints) + 1

        while True:
            try:
                label = label_prefix if counter == 0 else f'{label_prefix}_{counter}'
                group = AutoGroup(backend=self._backend, label=label).store()
                self._group_label = group.label
            except exceptions.IntegrityError:
                counter += 1
            else:
                break

        return group
