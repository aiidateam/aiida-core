###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :class:`aiida.orm.nodes.data.data:Data` class."""

import os

import numpy
import pytest

from aiida import orm, plugins
from tests.static import STATIC_DIR


@pytest.fixture
def generate_class_instance(tmp_path, chdir_tmp_path, aiida_localhost):
    """Generate a dummy `Data` instance for the given sub class."""

    def _generate_class_instance(data_class):
        if data_class is orm.CifData:
            instance = data_class(file=os.path.join(STATIC_DIR, 'data', 'Si.cif'))
            return instance

        if data_class is orm.UpfData:
            filename = os.path.join(STATIC_DIR, 'pseudos', 'Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF')
            instance = data_class(file=filename)
            return instance

        if data_class is orm.StructureData:
            instance = orm.CifData(file=os.path.join(STATIC_DIR, 'data', 'Si.cif')).get_structure()
            return instance

        if data_class is orm.BandsData:
            kpoints = orm.KpointsData()
            kpoints.set_cell([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
            kpoints.set_kpoints([[0.0, 0.0, 0.0], [0.1, 0.1, 0.1]])
            instance = data_class()
            instance.set_kpointsdata(kpoints)
            instance.set_bands([[1.0, 2.0], [3.0, 4.0]])
            return instance

        if data_class is orm.TrajectoryData:
            instance = data_class()
            stepids = numpy.array([60])
            times = stepids * 0.01
            cells = numpy.array([[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]]])
            positions = numpy.array([[[0.0, 0.0, 0.0]]])
            instance.set_trajectory(stepids=stepids, cells=cells, symbols=['H'], positions=positions, times=times)
            return instance

        if data_class is orm.UpfData:
            filepath_base = os.path.abspath(os.path.join(STATIC_DIR, 'pseudos'))
            filepath_carbon = os.path.join(filepath_base, 'C_pbe_v1.2.uspp.F.UPF')
            instance = data_class(file=filepath_carbon)
            return instance

        if data_class is orm.ArrayData:
            instance = data_class()
            array_data = numpy.identity(3)
            instance.set_array('data', array_data)
            instance.set_array('contains_nan_inf', numpy.array([float('NaN'), float('Inf')]))
            return instance

        if data_class is orm.KpointsData:
            instance = data_class()
            cell = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
            instance.set_cell(cell)
            instance.set_kpoints_mesh_from_density(0.5)
            return instance

        if data_class is orm.XyData:
            instance = data_class()
            instance.set_x(numpy.arange(5), 'xdata', 'm')
            instance.set_y(numpy.arange(5), 'ydata', 'm')
            return instance

        if data_class is orm.ProjectionData:
            my_real_hydrogen_dict = {
                'angular_momentum': -3,
                'diffusivity': None,
                'kind_name': 'As',
                'magnetic_number': 0,
                'position': [-1.420047044832945, 1.420047044832945, 1.420047044832945],
                'radial_nodes': 0,
                'spin': 0,
                'spin_orientation': None,
                'x_orientation': None,
                'z_orientation': None,
            }
            kpoints = orm.KpointsData()
            kpoints.set_cell([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
            kpoints.set_kpoints([[0.0, 0.0, 0.0]])
            bands = orm.BandsData()
            bands.set_kpointsdata(kpoints)
            bands.set_bands([[1.0]])

            RealHydrogen = plugins.OrbitalFactory('core.realhydrogen')  # noqa: N806
            orbital = RealHydrogen(**my_real_hydrogen_dict)

            instance = data_class()
            instance.set_reference_bandsdata(bands)
            instance.set_projectiondata(
                orbital, list_of_pdos=numpy.asarray([1.0]), list_of_energy=numpy.asarray([1.0]), bands_check=False
            )
            return instance

        if data_class is orm.AbstractCode:
            instance = data_class(label='test_abstract_code', remote_computer_exec=(aiida_localhost, '/bin/cat'))
            return instance

        if data_class is orm.Code:
            instance = data_class(label='test_code', remote_computer_exec=(aiida_localhost, '/bin/cat'))
            return instance

        if data_class is orm.InstalledCode:
            instance = data_class(
                label='test_installed_code',
                computer=aiida_localhost,
                filepath_executable='/bin/cat',
            )
            return instance

        if data_class is orm.PortableCode:
            (tmp_path / 'bash').touch()
            filepath_executable = 'bash'
            instance = data_class(
                label='test_portable_code',
                filepath_executable=filepath_executable,
                filepath_files=tmp_path,
            )
            return instance

        if data_class is orm.ContainerizedCode:
            return orm.ContainerizedCode(
                label='test_containerized_code',
                computer=aiida_localhost,
                image_name='image',
                filepath_executable='bash',
                engine_command='docker {image_name}',
            )

        raise RuntimeError(
            'no instance generator implemented for class `{}`. If you have added a `_prepare_*` method '
            'for this data class, add a generator of a dummy instance here'.format(data_class)
        )

    return _generate_class_instance


@pytest.fixture(
    scope='function',
    params=[
        entry_point
        for entry_point in plugins.get_entry_points('aiida.data')
        if entry_point.name not in ('core.code', 'core.code.abstract')
    ],
)
def data_plugin(request):
    """Fixture that parametrizes over all the registered entry points of the ``aiida.data`` entry point group."""
    return request.param.load()


def test_constructor():
    """Test the constructor.

    Specifically, verify that the ``source`` attribute can be set through a keyword argument.
    """
    source = {'id': 1}
    node = orm.Data(source=source)
    assert isinstance(node, orm.Data)
    assert node.source == source


def test_data_exporters(data_plugin, generate_class_instance):
    """Verify that the return value of the export methods of all `Data` sub classes have the correct type.

    It should be a tuple where the first should be a byte string and the second a dictionary.
    """
    export_formats = data_plugin.get_export_formats()

    if not export_formats:
        return

    instance = generate_class_instance(data_plugin)

    for fileformat in export_formats:
        content, dictionary = instance._exportcontent(fileformat)
        assert isinstance(content, bytes)
        assert isinstance(dictionary, dict)
