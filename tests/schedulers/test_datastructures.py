###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.schedulers.test_datastructures` module."""

import pytest

from aiida.schedulers.datastructures import NodeNumberJobResource, ParEnvJobResource


class TestNodeNumberJobResource:
    """Tests for the :class:`~aiida.schedulers.datastructures.NodeNumberJobResource`."""

    @staticmethod
    def test_validate_resources():
        """Test the `validate_resources` method."""
        cls = NodeNumberJobResource

        with pytest.raises(ValueError):
            cls.validate_resources()

        # Missing required field
        with pytest.raises(ValueError):
            cls.validate_resources(num_machines=1)
        with pytest.raises(ValueError):
            cls.validate_resources(num_mpiprocs_per_machine=1)
        with pytest.raises(ValueError):
            cls.validate_resources(tot_num_mpiprocs=1)

        # Wrong field name
        with pytest.raises(ValueError):
            cls.validate_resources(num_machines=2, num_mpiprocs_per_machine=8, wrong_name=16)

        # Examples of wrong information (e.g., number of machines or of nodes < 0
        with pytest.raises(ValueError):
            cls.validate_resources(num_machines=0, num_mpiprocs_per_machine=8)
        with pytest.raises(ValueError):
            cls.validate_resources(num_machines=1, num_mpiprocs_per_machine=0)
        with pytest.raises(ValueError):
            cls.validate_resources(num_machines=1, tot_num_mpiprocs=0)
        with pytest.raises(ValueError):
            cls.validate_resources(num_mpiprocs_per_machine=1, tot_num_mpiprocs=0)

        # Examples of inconsistent information
        with pytest.raises(ValueError):
            cls.validate_resources(num_mpiprocs_per_machine=8, num_machines=2, tot_num_mpiprocs=32)

        with pytest.raises(ValueError):
            cls.validate_resources(num_mpiprocs_per_machine=8, tot_num_mpiprocs=15)

    @staticmethod
    def test_constructor():
        """Test that constructor defines all valid keys even if not all defined explicitly."""
        # Standard info
        job_resource = NodeNumberJobResource(num_machines=2, num_mpiprocs_per_machine=8)
        assert job_resource.num_machines == 2
        assert job_resource.num_mpiprocs_per_machine == 8
        assert job_resource.get_tot_num_mpiprocs() == 16

        # Redundant but consistent information
        job_resource = NodeNumberJobResource(num_machines=2, num_mpiprocs_per_machine=8, tot_num_mpiprocs=16)
        assert job_resource.num_machines == 2
        assert job_resource.num_mpiprocs_per_machine == 8
        assert job_resource.get_tot_num_mpiprocs() == 16

        # Other equivalent ways of specifying the information
        job_resource = NodeNumberJobResource(num_mpiprocs_per_machine=8, tot_num_mpiprocs=16)
        assert job_resource.num_machines == 2
        assert job_resource.num_mpiprocs_per_machine == 8
        assert job_resource.get_tot_num_mpiprocs() == 16

        # Other equivalent ways of specifying the information
        job_resource = NodeNumberJobResource(num_machines=2, tot_num_mpiprocs=16)
        assert job_resource.num_machines == 2
        assert job_resource.num_mpiprocs_per_machine == 8
        assert job_resource.get_tot_num_mpiprocs() == 16


class TestParEnvJobResource:
    """Tests for the :class:`~aiida.schedulers.datastructures.ParEnvJobResource`."""

    @staticmethod
    def test_validate_resources():
        """Test the `validate_resources` method."""
        cls = ParEnvJobResource

        with pytest.raises(ValueError):
            cls.validate_resources()

        # Missing required field
        with pytest.raises(ValueError):
            cls.validate_resources(parallel_env='env')
        with pytest.raises(ValueError):
            cls.validate_resources(tot_num_mpiprocs=1)

        # Wrong types
        with pytest.raises(ValueError):
            cls.validate_resources(parallel_env={}, tot_num_mpiprocs=1)
        with pytest.raises(ValueError):
            cls.validate_resources(parallel_env='env', tot_num_mpiprocs='test')
        with pytest.raises(ValueError):
            cls.validate_resources(parallel_env='env', tot_num_mpiprocs=0)

        # Wrong field name
        with pytest.raises(ValueError):
            cls.validate_resources(parallel_env='env', tot_num_mpiprocs=1, wrong_name=16)

    @staticmethod
    def test_constructor():
        """Test that constructor defines all valid keys even if not all defined explicitly."""
        job_resource = ParEnvJobResource(parallel_env='env', tot_num_mpiprocs=1)
        assert job_resource.parallel_env == 'env'
        assert job_resource.tot_num_mpiprocs == 1


def test_serialization():
    """Test the serialization/deserialization of JobInfo classes."""
    from datetime import datetime

    from aiida.schedulers.datastructures import JobInfo, JobState

    dict_serialized_content = {
        'job_id': '12723',
        'title': 'some title',
        'queue_name': 'some_queue',
        'account': 'my_account',
    }

    to_serialize = {'job_state': (JobState.QUEUED, 'job_state'), 'submission_time': (datetime.now(), 'date')}

    job_info = JobInfo()
    for key, val in dict_serialized_content.items():
        setattr(job_info, key, val)

    for key, (val, field_type) in to_serialize.items():
        setattr(job_info, key, val)
        # Also append to the dictionary for easier comparison later
        dict_serialized_content[key] = JobInfo.serialize_field(value=val, field_type=field_type)

    assert job_info.get_dict() == dict_serialized_content
    # Full loop via JSON, moving data from job_info to job_info2;
    # we check that the content is fully preserved
    job_info2 = JobInfo.load_from_serialized(job_info.serialize())
    assert job_info2.get_dict() == dict_serialized_content

    # Check that fields are properly re-serialized with the correct type
    assert job_info2.job_state == to_serialize['job_state'][0]
    # Check that fields are properly re-serialized with the correct type
    assert job_info2.submission_time == to_serialize['submission_time'][0]
