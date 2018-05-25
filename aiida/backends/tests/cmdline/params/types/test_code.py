#-*- coding: utf8 -*-
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.params.types import IdentifierParam, CodeParam
from aiida.orm import Code, Computer


class TestCodeParam(AiidaTestCase):

    @classmethod
    def setUpClass(cls):
        """
        Create some code to test the CodeParam parameter type for the command line infrastructure
        We create an initial code with a random name and then on purpose create two code with a name
        that matches exactly the ID and UUID, respectively, of the first one. This allows us to test
        the rules implemented to solve ambiguities that arise when determing the identifier type
        """
        super(TestCodeParam, cls).setUpClass()

        cls.param = CodeParam()
        cls.entity_01 = Code(remote_computer_exec=(cls.computer, '/bin/true')).store()
        cls.entity_02 = Code(remote_computer_exec=(cls.computer, '/bin/true')).store()
        cls.entity_03 = Code(remote_computer_exec=(cls.computer, '/bin/true')).store()

        cls.entity_01.label = 'computer_01'
        cls.entity_02.label = str(cls.entity_01.pk)
        cls.entity_03.label = str(cls.entity_01.uuid)

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
        Verify that using the STRING will retrieve the correct entity
        """
        identifier = '{}'.format(self.entity_01.label)
        result = self.param.convert(identifier, None, None)
        self.assertEquals(result.uuid, self.entity_01.uuid)

    def test_get_by_fullname(self):
        """
        Verify that using the STRING@machinename will retrieve the correct entity
        """
        identifier = '{}@{}'.format(self.entity_01.label, self.computer.name)
        result = self.param.convert(identifier, None, None)
        self.assertEquals(result.uuid, self.entity_01.uuid)

    def test_ambiguous_label_pk(self):
        """
        Situation: STRING of entity_02 is exactly equal to ID of entity_01

        Verify that using an ambiguous identifier gives precedence to the ID interpretation
        Appending the special ambiguity breaker character will force the identifier to be treated as a STRING
        """
        identifier = '{}'.format(self.entity_02.label)
        result = self.param.convert(identifier, None, None)
        self.assertEquals(result.uuid, self.entity_01.uuid)

        identifier = '{}{}'.format(self.entity_02.label, IdentifierParam.LABEL_AMBIGUITY_BREAKER_CHARACTER)
        result = self.param.convert(identifier, None, None)
        self.assertEquals(result.uuid, self.entity_02.uuid)

    def test_ambiguous_label_uuid(self):
        """
        Situation: STRING of entity_03 is exactly equal to UUID of entity_01

        Verify that using an ambiguous identifier gives precedence to the UUID interpretation
        Appending the special ambiguity breaker character will force the identifier to be treated as a STRING
        """
        identifier = '{}'.format(self.entity_03.label)
        result = self.param.convert(identifier, None, None)
        self.assertEquals(result.uuid, self.entity_01.uuid)

        identifier = '{}{}'.format(self.entity_03.label, IdentifierParam.LABEL_AMBIGUITY_BREAKER_CHARACTER)
        result = self.param.convert(identifier, None, None)
        self.assertEquals(result.uuid, self.entity_03.uuid)
