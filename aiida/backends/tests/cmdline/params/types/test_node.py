#-*- coding: utf8 -*-
from click import BadParameter
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.params.types import IdentifierParam, NodeParam
from aiida.orm import Node


class TestNodeParam(AiidaTestCase):

    @classmethod
    def setUpClass(cls):
        """
        Create some nodes to test the NodeParam parameter type for the command line infrastructure
        """
        super(TestNodeParam, cls).setUpClass()

        cls.param = NodeParam()
        cls.entity_01 = Node().store()

    def test_get_by_id(self):
        """
        Verify that using the ID will retrieve the correct entity
        """
        identifier = '{}'.format(self.entity_01.pk)
        result = self.param.convert(identifier, None, None)
        self.assertEquals(result.uuid, self.entity_01.uuid)

    def test_get_by_uuid(self):
        """
        Verify that using the UUID will retrieve the correct entity
        """
        identifier = '{}'.format(self.entity_01.uuid)
        result = self.param.convert(identifier, None, None)
        self.assertEquals(result.uuid, self.entity_01.uuid)

    def test_get_by_label(self):
        """
        Verify that using the STRING identifier will raise as the Node class does not have a STRING based identifier
        """
        identifier = '{}'.format('SOMERANDOMSTRING')

        with self.assertRaises(BadParameter):
            result = self.param.convert(identifier, None, None)
