###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `CalcJobNode` node sub class."""

import io

import pytest

from aiida.common import CalcJobState, LinkType
from aiida.orm import CalcJobNode, FolderData


class TestCalcJobNode:
    """Tests for the `CalcJobNode` node sub class."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_localhost):
        """Initialize the profile."""
        self.computer = aiida_localhost

    def test_get_set_state(self):
        """Test the `get_state` and `set_state` method."""
        node = CalcJobNode(
            computer=self.computer,
        )
        assert node.get_state() is None

        with pytest.raises(ValueError):
            node.set_state('INVALID')

        node.set_state(CalcJobState.UPLOADING)
        assert node.get_state() == CalcJobState.UPLOADING

        # Setting an illegal calculation job state, the `get_state` should not fail but return `None`
        node.base.attributes.set(node.CALC_JOB_STATE_KEY, 'INVALID')
        assert node.get_state() is None

    def test_get_scheduler_stdout(self):
        """Verify that the repository sandbox folder is cleaned after the node instance is garbage collected."""
        option_key = 'scheduler_stdout'
        option_value = '_scheduler-output.txt'
        stdout = 'some\nstandard output'

        # Note: cannot use pytest.mark.parametrize in unittest classes, so I just do a loop here
        for with_file in [True, False]:
            for with_option in [True, False]:
                node = CalcJobNode(
                    computer=self.computer,
                )
                node.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
                retrieved = FolderData()

                if with_file:
                    retrieved.base.repository._repository.put_object_from_filelike(
                        io.BytesIO(stdout.encode('utf-8')), option_value
                    )
                    retrieved.base.repository._update_repository_metadata()
                if with_option:
                    node.set_option(option_key, option_value)
                node.store()
                retrieved.store()
                retrieved.base.links.add_incoming(node, link_type=LinkType.CREATE, link_label='retrieved')

                # It should return `None` if no scheduler output is there (file not there, or option not set),
                # while it should return the content if both are set
                assert node.get_scheduler_stdout() == (stdout if with_file and with_option else None)

    def test_get_scheduler_stderr(self):
        """Verify that the repository sandbox folder is cleaned after the node instance is garbage collected."""
        option_key = 'scheduler_stderr'
        option_value = '_scheduler-error.txt'
        stderr = 'some\nstandard error'

        # Note: cannot use pytest.mark.parametrize in unittest classes, so I just do a loop here
        for with_file in [True, False]:
            for with_option in [True, False]:
                node = CalcJobNode(
                    computer=self.computer,
                )
                node.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
                retrieved = FolderData()

                if with_file:
                    retrieved.base.repository._repository.put_object_from_filelike(
                        io.BytesIO(stderr.encode('utf-8')), option_value
                    )
                    retrieved.base.repository._update_repository_metadata()
                if with_option:
                    node.set_option(option_key, option_value)
                node.store()
                retrieved.store()
                retrieved.base.links.add_incoming(node, link_type=LinkType.CREATE, link_label='retrieved')

                # It should return `None` if no scheduler output is there (file not there, or option not set),
                # while it should return the content if both are set
                assert node.get_scheduler_stderr() == (stderr if with_file and with_option else None)

    @pytest.mark.parametrize(
        'retrieve_list, exception, match',
        (
            ([], None, None),
            (['directive'], None, None),
            ([['path', '.', None]], None, None),
            ([['path', '.', 1]], None, None),
            ([['path', '.', 1], 'directive'], None, None),
            (1, TypeError, 'file retrieval directives has to be a list or tuple'),
            ([1], ValueError, r'invalid directive, not a list or tuple of length three: .*'),
            ([['str', 'str']], ValueError, r'invalid directive, not a list or tuple of length three: .*'),
            ([[1, 'str', 0]], ValueError, r'.*, first element has to be a string representing remote path'),
            ([['str', 1, 0]], ValueError, r'.*, second element has to be a string representing local path'),
            ([['s', 's', '0']], ValueError, r'.*, third element has to be an integer representing the depth'),
        ),
    )
    def test_set_retrieve_list(self, retrieve_list, exception, match):
        """Test the :meth:`aiida.orm.nodes.process.calculation.calcjob.CalcJobNode.set_retrieve_list`."""
        node = CalcJobNode()

        if exception:
            with pytest.raises(exception, match=match):
                node.set_retrieve_list(retrieve_list)
        else:
            node.set_retrieve_list(retrieve_list)
            assert node.get_retrieve_list() == retrieve_list
