###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.orm.nodes.data.pickled` module."""

import dill
import pytest

from aiida.orm import Node, PickledData, load_node


def test_constructor():
    """Test the constructor of :class:`~aiida.orm.nodes.data.pickled.PickledData`."""
    node = PickledData(None)
    assert isinstance(node, PickledData)


def test_get_unpickler_information():
    """Test :meth:`~aiida.orm.nodes.data.pickled.PickledData.get_unpickler_information`."""
    node = PickledData(None)
    assert node.get_unpickler_information() == ('dill._dill', 'loads', dill.__version__)


@pytest.mark.parametrize('obj', (None, 5, 'string', {'some': 'dict'}, Node))
def test_load(obj):
    """Test :meth:`~aiida.orm.nodes.data.pickled.PickledData.load`."""
    node = PickledData(obj)
    assert node.load() == obj

    node.store()
    assert node.load() == obj

    loaded = load_node(node.pk)
    assert loaded.load() == obj


def test_kwargs():
    """Test that kwargs passed to the constructor are forwarded to the pickler and stored in node's attributes."""
    pickled = PickledData(Node, recurse=True).store()
    assert pickled.base.attributes.get(PickledData.KEY_ATTRIBUTES_PICKLER_KWARGS) == {'recurse': True}

    with pytest.raises(TypeError, match="got an unexpected keyword argument 'unsupported_kwarg'"):
        pickled = PickledData(Node, unsupported_kwarg=True).store()
