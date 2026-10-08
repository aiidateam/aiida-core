###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.orm.nodes.data.array.array` module."""

import click
import numpy
import pytest
from click.testing import CliRunner

from aiida.cmdline.groups.dynamic import DynamicEntryPointCommandGroup
from aiida.orm import ArrayData, load_node


def test_read_stored():
    """Test reading an array from an ``ArrayData`` after storing and loading it."""
    array = numpy.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
    node = ArrayData()
    node.set_array(array=array, name='array')

    assert numpy.array_equal(node.get_array('array'), array)

    node.store()
    assert numpy.array_equal(node.get_array('array'), array)

    loaded = load_node(node.uuid)
    assert numpy.array_equal(loaded.get_array('array'), array)


def test_constructor():
    """Test the various construction options."""
    node = ArrayData()
    assert node.get_arraynames() == []

    arrays = numpy.array([1, 2])
    node = ArrayData.from_arrays(arrays)
    assert node.get_arraynames() == [ArrayData.default_array_name]
    assert (node.get_array(ArrayData.default_array_name) == arrays).all()

    arrays = {'a': numpy.array([1, 2]), 'b': numpy.array([3, 4])}
    node = ArrayData.from_arrays(arrays)
    assert sorted(node.get_arraynames()) == ['a', 'b']
    assert (node.get_array('a') == arrays['a']).all()
    assert (node.get_array('b') == arrays['b']).all()


def test_cli_repo_source_combines_inline_and_file_inputs(tmp_path):
    """Test the inline-array and .npy-file CLI forms populate one arrays source."""
    filepath = tmp_path / 'from_file.npy'
    numpy.save(filepath, numpy.array([3, 4]))

    model = ArrayData.cli_spec.validate(
        {
            'array': (('inline', '[1, 2]'),),
            'filepath': (filepath,),
        }
    )
    node = model.to_entity()

    assert sorted(node.get_arraynames()) == ['from_file', 'inline']
    assert numpy.array_equal(node.get_array('inline'), numpy.array([1, 2]))
    assert numpy.array_equal(node.get_array('from_file'), numpy.array([3, 4]))


def test_cli_repo_source_generates_multiple_options():
    """Test that one arrays source generates distinct repeatable Click options."""
    parameters = {parameter.name: parameter for parameter in ArrayData.cli_spec.parameters()}

    assert set(parameters) >= {'array', 'filepath'}
    assert 'attribute' not in parameters
    options = {}
    for name in ('array', 'filepath'):
        decorator = DynamicEntryPointCommandGroup.create_option(
            name,
            parameters[name].as_option_spec(),
        )
        options[name] = decorator(lambda: None).__click_params__[0]

    assert options['array'].opts == ['-a', '--array']
    assert not options['array'].prompt
    assert options['array'].multiple
    assert options['array'].nargs == 2
    assert options['filepath'].opts == ['-f', '--filepath']
    assert not options['filepath'].prompt
    assert options['filepath'].multiple


def test_cli_repo_source_click_parses_repeated_inputs(tmp_path):
    """Test that generated multi-form options parse repeated values into source inputs."""
    filepath = tmp_path / 'array.npy'
    filepath.touch()
    parameters = {parameter.name: parameter for parameter in ArrayData.cli_spec.parameters()}
    parsed = {}

    def callback(**kwargs):
        parsed.update(kwargs)

    command = click.command()(callback)

    for name in ('filepath', 'array'):
        command = DynamicEntryPointCommandGroup.create_option(
            name,
            parameters[name].as_option_spec(),
        )(command)

    result = CliRunner().invoke(
        command,
        ['-a', 'inline', '[1, 2]', '-a', 'second', '[3]', '-f', str(filepath)],
    )

    assert result.exit_code == 0
    assert parsed == {
        'array': (('inline', '[1, 2]'), ('second', '[3]')),
        'filepath': (filepath,),
    }


def test_cli_repo_source_rejects_duplicate_names(tmp_path):
    """Test that inputs from different CLI forms cannot overwrite the same array."""
    filepath = tmp_path / 'inline.npy'
    numpy.save(filepath, numpy.array([3, 4]))

    with pytest.raises(ValueError, match='duplicate paths'):
        ArrayData.cli_spec.validate(
            {
                'array': (('inline', '[1, 2]'),),
                'filepath': (filepath,),
            }
        )


def test_cli_repo_source_interactive_collector(tmp_path):
    """Test that the arrays collector accepts a mixed sequence of file and inline inputs."""
    filepath = tmp_path / 'from_file.npy'
    numpy.save(filepath, numpy.array([3, 4]))
    captured = {}
    group = DynamicEntryPointCommandGroup(
        command=lambda ctx, cls, model: captured.update(model=model),
        entry_point_group='aiida.data',
    )

    def create() -> None:
        group.call_command(
            click.get_current_context(),
            ArrayData,
            False,
            array=(),
            filepath=(),
        )

    command = click.command()(create)
    result = CliRunner().invoke(
        command,
        input=f'file\n{filepath}\narray\ninline\n[1, 2]\ndone\n',
    )
    assert result.exit_code == 0, result.output

    node = captured['model'].to_entity()

    assert sorted(node.get_arraynames()) == ['from_file', 'inline']
    assert numpy.array_equal(node.get_array('inline'), numpy.array([1, 2]))
    assert numpy.array_equal(node.get_array('from_file'), numpy.array([3, 4]))


def test_get_array():
    """Test :meth:`aiida.orm.nodes.data.array.array.ArrayData:get_array`."""
    node = ArrayData()
    with pytest.raises(ValueError, match='`name` not specified but the node contains no arrays'):
        node.get_array()

    node = ArrayData.from_arrays({'a': numpy.array([]), 'b': numpy.array([])})
    with pytest.raises(ValueError, match='`name` not specified but the node contains multiple arrays'):
        node.get_array()

    node = ArrayData.from_arrays({'a': numpy.array([1, 2])})
    assert (node.get_array() == numpy.array([1, 2])).all()

    node = ArrayData.from_arrays(numpy.array([1, 2]))
    assert (node.get_array() == numpy.array([1, 2])).all()
