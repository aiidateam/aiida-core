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
from archive_path import ZipPath
import pytest

from aiida import orm
from aiida.common import json
from aiida.common.exceptions import LicensingException
from aiida.common.links import LinkType
from aiida.tools.archive import create_archive, exceptions, import_archive


@pytest.mark.parametrize('entities', ['all', 'specific'])
def test_base_data_nodes(clear_database_before_test, tmp_path, entities):
    """Test ex-/import of Base Data nodes"""
    # producing values for each base type
    values = ('Hello', 6, -1.2399834e12, False)
    filename = str(tmp_path / 'export.aiida')

    # producing nodes:
    nodes = [cls(val).store() for val, cls in zip(values, (orm.Str, orm.Int, orm.Float, orm.Bool))]
    # my uuid - list to reload the node:
    uuids = [n.uuid for n in nodes]
    # exporting the nodes:
    if entities == 'all':
        create_archive(None, filename=filename)
    else:
        create_archive(nodes, filename=filename)
    # cleaning:
    clear_database_before_test.reset_db()
    # Importing back the data:
    import_archive(filename)
    # Checking whether values are preserved:
    for uuid, refval in zip(uuids, values):
        assert orm.load_node(uuid).value == refval


def test_calc_of_structuredata(clear_database_before_test, tmp_path, aiida_localhost):
    """Simple ex-/import of CalcJobNode with input StructureData"""
    struct = orm.StructureData()
    struct.store()

    calc = orm.CalcJobNode()
    calc.computer = aiida_localhost
    calc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})

    calc.add_incoming(struct, link_type=LinkType.INPUT_CALC, link_label='link')
    calc.store()
    calc.seal()

    pks = [struct.pk, calc.pk]

    attrs = {}
    for pk in pks:
        node = orm.load_node(pk)
        attrs[node.uuid] = {}
        for k in node.attributes.keys():
            attrs[node.uuid][k] = node.get_attribute(k)

    filename = str(tmp_path / 'export.aiida')

    create_archive([calc], filename=filename)

    clear_database_before_test.reset_db()

    import_archive(filename)
    for uuid, value in attrs.items():
        node = orm.load_node(uuid)
        for k in value.keys():
            assert value[k] == node.get_attribute(k)


def test_check_for_export_format_version(clear_database_before_test, tmp_path):
    """Test the check for the export format version."""
    # first create an archive
    struct = orm.StructureData()
    struct.store()
    filename = str(tmp_path / 'export.aiida')
    create_archive([struct], filename=filename)

    # now change its version only
    filename2 = str(tmp_path / 'export2.aiida')
    with ZipPath(filename, mode='r') as inpath:
        with ZipPath(filename2, mode='w') as outpath:
            for subpath in inpath.glob('**/*'):
                if subpath.is_dir():
                    (outpath / subpath.at).mkdir()
                elif subpath.at == 'metadata.json':
                    metadata = json.loads(subpath.read_text())
                    metadata['export_version'] = 0.0
                    (outpath / subpath.at).write_text(json.dumps(metadata))
                else:
                    (outpath / subpath.at).write_bytes(subpath.read_bytes())

    # then try to import it
    clear_database_before_test.reset_db()
    with pytest.raises(exceptions.IncompatibleArchiveVersionError):
        import_archive(filename2)


@pytest.mark.usefixtures('clear_database_before_test')
def test_control_of_licenses(tmp_path):
    """Test control of licenses."""
    struct = orm.StructureData()
    struct.source = {'license': 'GPL'}
    struct.store()

    # first check successful import
    create_archive([struct], filename=tmp_path / 'archive.aiida', allowed_licenses=['GPL'])
    create_archive([struct], filename=tmp_path / 'archive2.aiida', forbidden_licenses=['Academic'])

    # now check that the import fails
    with pytest.raises(LicensingException):
        create_archive([struct], test_run=True, allowed_licenses=['CC0'])

    with pytest.raises(LicensingException):
        create_archive([struct], test_run=True, forbidden_licenses=['GPL'])

    def cc_filter(license_):
        return license_.startswith('CC')

    def gpl_filter(license_):
        return license_ == 'GPL'

    def crashing_filter(_):
        raise NotImplementedError('not implemented yet')

    with pytest.raises(LicensingException):
        create_archive([struct], test_run=True, allowed_licenses=cc_filter)

    with pytest.raises(LicensingException):
        create_archive([struct], test_run=True, forbidden_licenses=gpl_filter)

    with pytest.raises(LicensingException):
        create_archive([struct], test_run=True, allowed_licenses=crashing_filter)

    with pytest.raises(LicensingException):
        create_archive([struct], test_run=True, forbidden_licenses=crashing_filter)
