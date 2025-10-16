###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Simple tests for the export and import routines"""

import functools
import json

import pytest
from archive_path import ZipPath

from aiida import orm
from aiida.common.exceptions import IncompatibleStorageSchema, LicensingException
from aiida.common.links import LinkType
from aiida.tools.archive import create_archive, import_archive


@pytest.mark.parametrize('entities', ['all', 'specific'])
def test_base_data_nodes(aiida_profile_clean, tmp_path, entities):
    """Test ex-/import of Base Data nodes"""
    # producing values for each base type
    values = ('Hello', 6, -1.2399834e12, False)
    filename = str(tmp_path / 'export.aiida')

    # Regression test for https://github.com/aiidateam/aiida-core/issues/6325
    # Test run should not fail for empty DB
    create_archive(None, filename=filename, test_run=True)

    # producing nodes:
    nodes = [cls(val).store() for val, cls in zip(values, (orm.Str, orm.Int, orm.Float, orm.Bool))]
    # my uuid - list to reload the node:
    uuids = [n.uuid for n in nodes]

    if entities == 'all':
        create = functools.partial(create_archive, None)
    else:
        create = functools.partial(create_archive, nodes)

    # check that test run succeeds
    create(filename=filename, test_run=True)
    # actually export now
    create(filename=filename)
    # cleaning:
    aiida_profile_clean.reset_storage()
    # Importing back the data:
    import_archive(filename)
    # Checking whether values are preserved:
    for uuid, refval in zip(uuids, values):
        assert orm.load_node(uuid).value == refval


def test_calc_of_structuredata(aiida_profile, tmp_path, aiida_localhost):
    """Simple ex-/import of CalcJobNode with input StructureData"""
    struct = orm.StructureData(pbc=False)
    struct.store()

    calc = orm.CalcJobNode()
    calc.computer = aiida_localhost
    calc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})

    calc.base.links.add_incoming(struct, link_type=LinkType.INPUT_CALC, link_label='link')
    calc.store()
    calc.seal()

    pks = [struct.pk, calc.pk]

    attrs = {}
    for pk in pks:
        node = orm.load_node(pk)
        attrs[node.uuid] = {}
        for k in node.base.attributes.keys():
            attrs[node.uuid][k] = node.base.attributes.get(k)

    filename = str(tmp_path / 'export.aiida')

    create_archive([calc], filename=filename)

    aiida_profile.reset_storage()

    import_archive(filename)
    for uuid, value in attrs.items():
        node = orm.load_node(uuid)
        for k in value.keys():
            assert value[k] == node.base.attributes.get(k)


def test_check_for_export_format_version(aiida_profile, tmp_path):
    """Test the check for the export format version."""
    # first create an archive
    struct = orm.StructureData(pbc=False)
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
    aiida_profile.reset_storage()
    with pytest.raises(IncompatibleStorageSchema):
        import_archive(filename2)


def test_control_of_licenses(tmp_path):
    """Test control of licenses."""
    struct = orm.StructureData(pbc=False)
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


def test_export_filter_size(tmp_path, aiida_profile_clean):
    """Test that export still works when the number of entities exceeds filter_size limit."""
    # Create multiple entities that will trigger filter_size batching
    nb_nodes = 5
    nodes = []
    for i in range(nb_nodes):
        node = orm.Int(i)
        node.label = f'node_{i}'
        node.store()
        nodes.append(node)

    # Export with a small filter_size to force batching
    export_file = tmp_path / 'export.aiida'
    create_archive(nodes, filename=export_file, filter_size=2)

    # Verify export was successful by importing and checking
    aiida_profile_clean.reset_storage()
    import_archive(export_file)

    # Check all nodes were exported/imported correctly
    builder = orm.QueryBuilder().append(orm.Node, project=['label'])
    imported_nodes = builder.all(flat=True)

    assert len(imported_nodes) == nb_nodes
    expected_labels = [f'node_{i}' for i in range(nb_nodes)]
    assert set(imported_nodes) == set(expected_labels)
