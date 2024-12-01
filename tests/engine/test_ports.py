###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for process spec ports."""

import pytest

from aiida.engine.processes.ports import InputPort, PortNamespace
from aiida.orm import Dict, Int, to_aiida_type


class TestInputPort:
    """Tests for the `InputPort` class."""

    def test_with_non_db(self):
        """Test the functionality of the `non_db` attribute upon construction and setting."""
        # When not specifying, it should get the default value and `non_db_explicitly_set` should be `False`
        port = InputPort('port')
        assert port.non_db is False
        assert port.non_db_explicitly_set is False

        # Using the setter to change the value should toggle both properties
        port.non_db = True
        assert port.non_db is True
        assert port.non_db_explicitly_set is True

        # Explicitly setting to `False` upon construction
        port = InputPort('port', non_db=False)
        assert port.non_db is False
        assert port.non_db_explicitly_set is True

        # Explicitly setting to `True` upon construction
        port = InputPort('port', non_db=True)
        assert port.non_db is True
        assert port.non_db_explicitly_set is True


class TestPortNamespace:
    """Tests for the `PortNamespace` class."""

    def test_with_non_db(self):
        """Ports inserted to a `PortNamespace` should inherit the `non_db` attribute if not explicitly set."""
        namespace_non_db = True
        port_namespace = PortNamespace('namespace', non_db=namespace_non_db)

        # When explicitly set upon port construction, value should not be inherited even when different
        port = InputPort('storable', non_db=False)
        port_namespace['storable'] = port
        assert port.non_db is False

        port = InputPort('not_storable', non_db=True)
        port_namespace['not_storable'] = port
        assert port.non_db is True

        # If not explicitly defined, it should inherit from parent namespace
        port = InputPort('not_storable')
        port_namespace['not_storable'] = port
        assert port.non_db == namespace_non_db

    def test_validate_port_name(self):
        """This test will ensure that illegal port names will raise a `ValueError` when trying to add it."""
        port = InputPort('port')
        port_namespace = PortNamespace('namespace')

        illegal_port_names = [
            'two__underscores',
            'three___underscores',
            '_leading_underscore',
            'trailing_underscore_',
            'non_numeric_%',
            'including.period',
            'disallowed👻unicodecharacters',
            'white space',
            'das-hes',
        ]

        for port_name in illegal_port_names:
            with pytest.raises(ValueError):
                port_namespace[port_name] = port

    def test_serialize_type_check(self):
        """Test that `serialize` will include full port namespace in exception message."""
        base_namespace = 'base'
        nested_namespace = 'some.nested.namespace'
        port_namespace = PortNamespace(base_namespace)
        port_namespace.create_port_namespace(nested_namespace)

        with pytest.raises(TypeError, match=f'.*{base_namespace}.*{nested_namespace}.*'):
            port_namespace.serialize({'some': {'nested': {'namespace': Dict()}}})

    def test_lambda_default(self):
        """Test that an input port can specify a lambda as a default."""
        port_namespace = PortNamespace('base')

        # Defining lambda for default that returns incorrect type should not except at construction
        port_namespace['port'] = InputPort('port', valid_type=Int, default=lambda: 'string')

        # However, pre processing the namespace, which shall evaluate the default followed by validation will fail
        inputs = port_namespace.pre_process({})
        assert port_namespace.validate(inputs) is not None

        # Passing an explicit value for the port will forego the default and validation on returned inputs should pass
        inputs = port_namespace.pre_process({'port': Int(5)})
        assert port_namespace.validate(inputs) is None

        # Redefining the port, this time with a correct default
        port_namespace['port'] = InputPort('port', valid_type=Int, default=lambda: Int(5))

        # Pre processing the namespace shall evaluate the default and return the int node
        inputs = port_namespace.pre_process({})
        assert isinstance(inputs['port'], Int)
        assert inputs['port'].value == 5

        # Passing an explicit value for the port will forego the default
        inputs = port_namespace.pre_process({'port': Int(3)})
        assert isinstance(inputs['port'], Int)
        assert inputs['port'].value == 3

    @pytest.mark.parametrize('is_metadata', (True, False))
    def test_serializer(self, is_metadata):
        """Test the automatic setting of the serializer for non-metadata ports.

        For non-metadata portnamespaces, the serializer should be automatically set to the
        :meth:`aiida.orm.nodes.data.base.to_aiida_type` serializer, unless the port already defines a serializer itself.
        """
        namespace = PortNamespace('namespace', is_metadata=is_metadata)
        port = InputPort('port')
        namespace['port'] = port

        if is_metadata:
            assert port.serializer is None
        else:
            assert port.serializer is to_aiida_type

        def custom_serializer(*args, **kwargs):
            pass

        other_port = InputPort('other_port', serializer=custom_serializer)
        namespace['other_port'] = port
        assert other_port.serializer is custom_serializer
