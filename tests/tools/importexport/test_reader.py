# -*- coding: utf-8 -*-
from aiida.tools.importexport.dbimport.readers import ReaderJsonZip

PATH = '/Users/chrisjsewell/Documents/GitHub/aiida_core_develop/out.aiida'


def test_basic():
    with ReaderJsonZip(PATH) as reader:
        assert reader.metadata.export_version == '0.9'
        assert reader.metadata.aiida_version == '1.4.2'
        assert sorted(reader.entity_names) == ['Comment', 'Computer', 'Group', 'Log', 'Node', 'User']
        assert reader.entity_count('Node') == 40065
        assert sum(1 for _ in reader.iter_entity_fields('Node')) == 40065
        assert reader.entity_count('Computer') == None
        assert reader.entity_count('User') == 1
        assert reader.entity_count('Group') == None
        assert sum(1 for _ in reader.iter_group_uuids()) == 0
        assert reader.link_count == 40064
        assert sum(1 for _ in reader.iter_link_uuids()) == 40064
        assert next(reader.iter_entity_fields('Node', fields=('label', 'node_type', 'attributes'))) == (
            15663, 'uuid', {
                'node_type': 'data.dict.Dict.',
                'label': '',
                'attributes': {
                    '0': 0,
                    '1': 1,
                    '2': 2,
                    '3': 3,
                    '4': 4,
                    '5': 5,
                    '6': 6,
                    '7': 7,
                    '8': 8,
                    '9': 9
                }
            }
        )
