###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Fixtures for the tests of the parser plugins."""

from __future__ import annotations

import collections
import pathlib

import pytest

from aiida.common.links import LinkType
from aiida.orm import CalcJobNode, FolderData
from aiida.plugins import ParserFactory


@pytest.fixture
def parse_calc_job(generate_shell_calc_job_node, generate_parser):
    """Mock a ``CalcJobNode``, instantiate a ``Parser`` and then call :meth:`aiida.parsers.Parser.parse_from_node`."""

    def factory(entry_point_name='core.shell', store_provenance=False, filepath_retrieved_temporary=None, inputs=None):
        """Create fixture.

        :param entry_point_name: entry point name to be used for the mocked ``CalcJobNode``.
        :param store_provenace: whether to store the provenance of the parsing.
        :param filepath_retrieved_temporary: path to temporary retrieved folder.
        :param inputs: dictionary of inputs to add to the mocked ``CalcJobNode``.
        :returns: tuple of the mocked ``CalcJobNode``, the parsed results and the calcfunction node representing the
            parsing action.
        """
        node = generate_shell_calc_job_node(inputs=inputs)
        parser = generate_parser(entry_point_name)
        results, calcfunction = parser.parse_from_node(
            node, store_provenance=store_provenance, retrieved_temporary_folder=filepath_retrieved_temporary
        )
        return node, results, calcfunction

    return factory


@pytest.fixture
def generate_shell_calc_job_node(aiida_localhost):
    """Create and return a :class:`aiida.orm.CalcJobNode` instance."""

    def flatten_inputs(inputs, prefix=''):
        """Flatten inputs recursively like :meth:`aiida.engine.processes.process::Process._flatten_inputs`."""
        flat_inputs = []
        for key, value in inputs.items():
            if isinstance(value, collections.abc.Mapping):
                flat_inputs.extend(flatten_inputs(value, prefix=prefix + key + '__'))
            else:
                flat_inputs.append((prefix + key, value))
        return flat_inputs

    def factory(filepath_retrieved: pathlib.Path | None = None, inputs: dict | None = None):
        """Create and return a :class:`aiida.orm.CalcJobNode` instance."""
        node = CalcJobNode(computer=aiida_localhost, process_type='aiida.calculations:core.shell')
        node.set_retrieve_list(['stdout'])

        if inputs:
            for link_label, input_node in flatten_inputs(inputs):
                input_node.store()
                node.base.links.add_incoming(input_node, link_type=LinkType.INPUT_CALC, link_label=link_label)

        node.store()
        retrieved = FolderData()

        if filepath_retrieved:
            retrieved.put_object_from_tree(filepath_retrieved)

        retrieved.base.links.add_incoming(node, link_type=LinkType.CREATE, link_label='retrieved')
        retrieved.store()

        return node

    return factory


@pytest.fixture(scope='session')
def generate_parser():
    """Load and return a :class:`aiida.parsers.Parser` from an entry point."""

    def factory(entry_point_name):
        """Load and return a :class:`aiida.parsers.Parser` from an entry point.

        :param entry_point_name: entry point name of the parser class.
        :return: the loaded parser plugin.
        """
        return ParserFactory(entry_point_name)

    return factory
