# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Simple tests for the export and import routines"""
import tarfile

import pytest

from aiida import orm
from aiida.common import json
from aiida.common.exceptions import LicensingException
from aiida.common.folders import SandboxFolder
from aiida.common.links import LinkType
from aiida.tools.importexport import import_data, export
from aiida.tools.importexport.common import exceptions


@pytest.mark.parametrize('file_format', ('zip', 'tar.gz'))
def test_base_data_nodes(aiida_profile, tmp_path, file_format):
    """Test ex-/import of Base Data nodes"""
    aiida_profile.reset_db()

    # producing values for each base type
    values = ('Hello', 6, -1.2399834e12, False)  # , ["Bla", 1, 1e-10])
    filename = str(tmp_path / 'export.aiida')

    # producing nodes:
    nodes = [cls(val).store() for val, cls in zip(values, (orm.Str, orm.Int, orm.Float, orm.Bool))]
    # my uuid - list to reload the node:
    uuids = [n.uuid for n in nodes]
    # exporting the nodes:
    export(nodes, filename=filename, file_format=file_format)
    # cleaning:
    aiida_profile.reset_db()
    # Importing back the data:
    import_data(filename)
    # Checking whether values are preserved:
    for uuid, refval in zip(uuids, values):
        assert orm.load_node(uuid).value == refval


@pytest.mark.parametrize('file_format', ('zip', 'tar.gz'))
def test_calc_of_structuredata(aiida_profile, tmp_path, file_format):
    """Simple ex-/import of CalcJobNode with input StructureData"""
    aiida_profile.reset_db()

    struct = orm.StructureData()
    struct.store()

    computer = orm.Computer(
        label='localhost-test',
        description='localhost computer set up by test manager',
        hostname='localhost-test',
        workdir=str(tmp_path / 'workdir'),
        transport_type='local',
        scheduler_type='direct'
    )
    computer.store()
    computer.configure()

    calc = orm.CalcJobNode()
    calc.computer = computer
    calc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})

    calc.add_incoming(struct, link_type=LinkType.INPUT_CALC, link_label='link')
    calc.store()
    calc.seal()

    pks = [struct.pk, calc.pk]

    attrs = {}
    for pk in pks:
        node = orm.load_node(pk)
        attrs[node.uuid] = dict()
        for k in node.attributes.keys():
            attrs[node.uuid][k] = node.get_attribute(k)

    filename = str(tmp_path / 'export.aiida')

    export([calc], filename=filename, file_format=file_format)

    aiida_profile.reset_db()

    import_data(filename)
    for uuid in attrs:
        node = orm.load_node(uuid)
        for k in attrs[uuid].keys():
            assert attrs[uuid][k] == node.get_attribute(k)


def test_check_for_export_format_version(aiida_profile, tmp_path):
    """Test the check for the export format version."""
    # Creating a folder for the archive files
    export_file_tmp_folder = tmp_path / 'export_tmp'
    export_file_tmp_folder.mkdir()
    unpack_tmp_folder = tmp_path / 'unpack_tmp'
    unpack_tmp_folder.mkdir()

    aiida_profile.reset_db()

    struct = orm.StructureData()
    struct.store()

    filename = str(export_file_tmp_folder / 'export.aiida')
    export([struct], filename=filename, file_format='tar.gz')

    with tarfile.open(filename, 'r:gz', format=tarfile.PAX_FORMAT) as tar:
        tar.extractall(unpack_tmp_folder)

    with (unpack_tmp_folder / 'metadata.json').open('r', encoding='utf8') as fhandle:
        metadata = json.load(fhandle)
    metadata['export_version'] = 0.0

    with (unpack_tmp_folder / 'metadata.json').open('wb') as fhandle:
        json.dump(metadata, fhandle)

    with tarfile.open(filename, 'w:gz', format=tarfile.PAX_FORMAT) as tar:
        tar.add(unpack_tmp_folder, arcname='')

    aiida_profile.reset_db()

    with pytest.raises(exceptions.IncompatibleArchiveVersionError):
        import_data(filename)


@pytest.mark.usefixtures('clear_database_before_test')
def test_control_of_licenses():
    """Test control of licenses."""
    struct = orm.StructureData()
    struct.source = {'license': 'GPL'}
    struct.store()

    folder = SandboxFolder()
    export([struct], file_format='folder', writer_init={'folder': folder}, allowed_licenses=['GPL'])
    # Folder should contain two files of metadata + nodes/
    assert len(folder.get_content_list()) == 3

    folder.erase(create_empty_folder=True)
    assert len(folder.get_content_list()) == 0
    export([struct], file_format='folder', writer_init={'folder': folder}, forbidden_licenses=['Academic'])
    # Folder should contain two files of metadata + nodes/
    assert len(folder.get_content_list()) == 3

    with pytest.raises(LicensingException):
        export([struct], file_format='null', allowed_licenses=['CC0'])

    with pytest.raises(LicensingException):
        export([struct], file_format='null', forbidden_licenses=['GPL'])

    def cc_filter(license_):
        return license_.startswith('CC')

    def gpl_filter(license_):
        return license_ == 'GPL'

    def crashing_filter():
        raise NotImplementedError('not implemented yet')

    with pytest.raises(LicensingException):
        export([struct], file_format='null', allowed_licenses=cc_filter)

    with pytest.raises(LicensingException):
        export([struct], file_format='null', forbidden_licenses=gpl_filter)

    with pytest.raises(LicensingException):
        export([struct], file_format='null', allowed_licenses=crashing_filter)

    with pytest.raises(LicensingException):
        export([struct], file_format='null', forbidden_licenses=crashing_filter)
