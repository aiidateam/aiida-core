###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `ProcessSpec` class."""

import pytest

from aiida.engine import Process, ProcessSpec
from aiida.orm import Data, Node


class TestProcessSpec:
    """Tests for the `ProcessSpec` class."""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        assert Process.current() is None
        self.spec = Process.spec()
        self.spec.inputs.valid_type = Data
        self.spec.outputs.valid_type = Data
        yield
        assert Process.current() is None

    @pytest.mark.parametrize(
        ('expose_method', 'memory_attribute'),
        (
            ('expose_inputs', '_exposed_inputs'),
            ('expose_outputs', '_exposed_outputs'),
        ),
    )
    def test_repeated_exposure_accumulates_ports(self, expose_method, memory_attribute):
        """Test repeated calls accumulate the exposed ports for a process class."""

        class ChildProcess(Process):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.input('first')
                spec.input('second')
                spec.output('first')
                spec.output('second')

        spec = ProcessSpec()
        expose = getattr(spec, expose_method)
        expose(ChildProcess, include=('first',))
        expose(ChildProcess, include=('second',))

        assert getattr(spec, memory_attribute)[None][ChildProcess] == ['first', 'second']

    def test_dynamic_input(self):
        """Test a process spec with dynamic input enabled."""
        node = Node()
        data = Data()
        assert self.spec.inputs.validate({'key': 'foo'}) is not None
        assert self.spec.inputs.validate({'key': 5}) is not None
        assert self.spec.inputs.validate({'key': node}) is not None
        assert self.spec.inputs.validate({'key': data}) is None

    def test_dynamic_output(self):
        """Test a process spec with dynamic output enabled."""
        node = Node()
        data = Data()
        assert self.spec.outputs.validate({'key': 'foo'}) is not None
        assert self.spec.outputs.validate({'key': 5}) is not None
        assert self.spec.outputs.validate({'key': node}) is not None
        assert self.spec.outputs.validate({'key': data}) is None

    def test_exit_code(self):
        """Test the definition of error codes through the ProcessSpec."""
        label = 'SOME_EXIT_CODE'
        status = 418
        message = 'I am a teapot'

        self.spec.exit_code(status, label, message)

        assert self.spec.exit_codes.SOME_EXIT_CODE.status == status
        assert self.spec.exit_codes.SOME_EXIT_CODE.message == message

        assert self.spec.exit_codes['SOME_EXIT_CODE'].status == status
        assert self.spec.exit_codes['SOME_EXIT_CODE'].message == message

        assert self.spec.exit_codes[label].status == status
        assert self.spec.exit_codes[label].message == message

    def test_exit_code_invalid(self):
        """Test type validation for registering new error codes."""
        status = 418
        label = 'SOME_EXIT_CODE'
        message = 'I am a teapot'

        with pytest.raises(TypeError):
            self.spec.exit_code(status, 256, message)

        with pytest.raises(TypeError):
            self.spec.exit_code('string', label, message)

        with pytest.raises(ValueError):
            self.spec.exit_code(-256, label, message)

        with pytest.raises(TypeError):
            self.spec.exit_code(status, label, 8)
