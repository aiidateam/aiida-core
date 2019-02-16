# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Tests for nodes, attributes and links
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import LinkType
from aiida.orm import Data, Node
from aiida.orm import CalculationNode


class TestNodeBasicDjango(AiidaTestCase):
    def test_replace_extras_2(self):
        """
        This is a Django specific test which checks (manually) that,
        when replacing list and dict with objects that have no deepness,
        no junk is left in the DB (i.e., no 'dict.a', 'list.3.h', ...
        """
        from aiida.backends.djsite.db.models import DbExtra

        a = Data().store()
        extras_to_set = {
            'bool': True,
            'integer': 12,
            'float': 26.2,
            'string': "a string",
            'dict': {"a": "b",
                     "sublist": [1, 2, 3],
                     "subdict": {
                         "c": "d"}},
            'list': [1, True, "ggg", {'h': 'j'}, [9, 8, 7]],
        }

        # I redefine the keys with more complicated data, and
        # changing the data type too
        new_extras = {
            'bool': 12,
            'integer': [2, [3], 'a'],
            'float': {'n': 'm', 'x': [1, 'r', {}]},
            'string': True,
            'dict': 'text',
            'list': 66.3,
        }

        for k, v in extras_to_set.items():
            a.set_extra(k, v)

        for k, v in new_extras.items():
            # I delete one by one the keys and check if the operation is
            # performed correctly
            a.set_extra(k, v)

        # I update extras_to_set with the new entries, and do the comparison
        # again
        extras_to_set.update(new_extras)

        # Check (manually) that, when replacing list and dict with objects
        # that have no deepness, no junk is left in the DB (i.e., no
        # 'dict.a', 'list.3.h', ...
        self.assertEquals(len(DbExtra.objects.filter(
            dbnode=a.backend_entity.dbmodel, key__startswith=('list' + DbExtra._sep))), 0)
        self.assertEquals(len(DbExtra.objects.filter(
            dbnode=a.backend_entity.dbmodel, key__startswith=('dict' + DbExtra._sep))), 0)

    def test_attrs_and_extras_wrong_keyname(self):
        """
        Attribute keys cannot include the separator symbol in the key
        """
        from aiida.backends.djsite.db.models import DbAttributeBaseClass
        from aiida.common.exceptions import ModificationNotAllowed, ValidationError

        separator = DbAttributeBaseClass._sep

        a = Data().store()

        with self.assertRaises(ModificationNotAllowed):
            # Cannot change an attribute on a stored node
            a.set_attribute('name' + separator, 'blablabla')

        with self.assertRaises(ValidationError):
            # Cannot change an attribute on a stored node
            a.set_attribute('name' + separator, 'blablabla', stored_check=False)

        with self.assertRaises(ValidationError):
            # Passing an attribute key separator directly in the key is not allowed
            a.set_extra('bool' + separator, 'blablabla')

    def test_settings(self):
        """
        Test the settings table (similar to Attributes, but without the key.
        """
        from aiida.backends.djsite.db import models
        from django.db import IntegrityError, transaction

        models.DbSetting.set_value(key='pippo', value=[1, 2, 3])

        s1 = models.DbSetting.objects.get(key='pippo')

        self.assertEqual(s1.getvalue(), [1, 2, 3])

        s2 = models.DbSetting(key='pippo')

        sid = transaction.savepoint()
        with self.assertRaises(IntegrityError):
            # same name...
            s2.save()
        transaction.savepoint_rollback(sid)

        # Should replace pippo
        models.DbSetting.set_value(key='pippo', value="a")
        s1 = models.DbSetting.objects.get(key='pippo')

        self.assertEqual(s1.getvalue(), "a")

    def test_load_nodes(self):
        """
        """
        from aiida.orm import load_node

        a = Data()
        a.store()
        self.assertEquals(a.pk, load_node(pk=a.pk).pk)
        self.assertEquals(a.pk, load_node(uuid=a.uuid).pk)

        with self.assertRaises(ValueError):
            load_node(identifier=a.pk, pk=a.pk)
        with self.assertRaises(ValueError):
            load_node(pk=a.pk, uuid=a.uuid)
        with self.assertRaises(TypeError):
            load_node(pk=a.uuid)
        with self.assertRaises(TypeError):
            load_node(uuid=a.pk)
        with self.assertRaises(ValueError):
            load_node()
