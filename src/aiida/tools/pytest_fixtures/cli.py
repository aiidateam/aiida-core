###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""CLI-related pytest fixtures and checks."""

from __future__ import annotations

import click
import pytest


def assert_verdi_group_option_names_do_not_overlap_with_ancestors() -> None:
    """Assert built-in and plugin-provided ``verdi`` groups do not reuse ancestor option names."""
    from aiida.cmdline.commands import cmd_verdi

    ignored_option_names = {'verbosity'}

    def recurse(
        command: click.Command, path: tuple[str, ...] = (), ancestor_option_names: tuple[set[str], ...] = ()
    ) -> None:
        if not isinstance(command, click.Group):
            return

        command_name = command.name or '<unnamed>'
        current_path = path + (command_name,)
        own_option_names = {
            parameter.name
            for parameter in command.params
            if isinstance(parameter, click.Option)
            and parameter.name is not None
            and parameter.name not in ignored_option_names
        }
        inherited_option_names = set().union(*ancestor_option_names) if ancestor_option_names else set()
        overlap = own_option_names & inherited_option_names

        assert not overlap, f'group `{" ".join(current_path)}` reuses ancestor option names: {sorted(overlap)}'

        context = click.Context(command)

        for command_name in command.list_commands(context):
            subcommand = command.get_command(context, command_name)
            if subcommand is None:
                continue
            recurse(subcommand, current_path, (*ancestor_option_names, own_option_names))

    recurse(cmd_verdi.verdi)


@pytest.fixture(scope='session', autouse=True)
def check_verdi_group_option_names() -> None:
    """Check the ``verdi`` CLI tree for ancestor/descendant option-name collisions."""
    assert_verdi_group_option_names_do_not_overlap_with_ancestors()
