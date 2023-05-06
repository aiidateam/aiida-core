# -*- coding: utf-8 -*-
"""Tests for :mod:`aiida.orm.nodes.process.process`."""
from aiida.engine import ExitCode
from aiida.orm.nodes.process.process import ProcessNode


def test_exit_code():
    """Test the :meth:`aiida.orm.nodes.process.process.ProcessNode.exit_code` property."""
    node = ProcessNode()
    assert node.exit_code is None

    node.set_exit_status(418)
    assert node.exit_code is None

    node.set_exit_message('I am a teapot')
    assert node.exit_code == ExitCode(418, 'I am a teapot')
