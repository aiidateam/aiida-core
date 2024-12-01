###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `DataParamType`."""

import uuid

import pytest

from aiida.cmdline.params.types import DataParamType
from aiida.orm import Data
from aiida.orm.utils.loaders import OrmEntityLoader


class TestDataParamType:
    """Tests for the `DataParamType`."""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Create some code to test the DataParamType parameter type for the command line infrastructure
        We create an initial code with a random name and then on purpose create two code with a name
        that matches exactly the ID and UUID, respectively, of the first one. This allows us to test
        the rules implemented to solve ambiguities that arise when determing the identifier type
        """
        self.param = DataParamType()
        self.entity_01 = Data().store()
        self.entity_02 = Data().store()
        self.entity_03 = Data().store()

        self.entity_01.label = f'data-{uuid.uuid4()}'
        self.entity_02.label = str(self.entity_01.pk)
        self.entity_03.label = str(self.entity_01.uuid)

    def test_get_by_id(self):
        """Verify that using the ID will retrieve the correct entity"""
        identifier = f'{self.entity_01.pk}'
        result = self.param.convert(identifier, None, None)
        assert result.uuid == self.entity_01.uuid

    def test_get_by_uuid(self):
        """Verify that using the UUID will retrieve the correct entity"""
        identifier = f'{self.entity_01.uuid}'
        result = self.param.convert(identifier, None, None)
        assert result.uuid == self.entity_01.uuid

    def test_get_by_label(self):
        """Verify that using the LABEL will retrieve the correct entity"""
        identifier = f'{self.entity_01.label}'
        result = self.param.convert(identifier, None, None)
        assert result.uuid == self.entity_01.uuid

    def test_ambiguous_label_pk(self):
        """Situation: LABEL of entity_02 is exactly equal to ID of entity_01

        Verify that using an ambiguous identifier gives precedence to the ID interpretation
        Appending the special ambiguity breaker character will force the identifier to be treated as a LABEL
        """
        identifier = f'{self.entity_02.label}'
        result = self.param.convert(identifier, None, None)
        assert result.uuid == self.entity_01.uuid

        identifier = f'{self.entity_02.label}{OrmEntityLoader.label_ambiguity_breaker}'
        result = self.param.convert(identifier, None, None)
        assert result.uuid == self.entity_02.uuid

    def test_ambiguous_label_uuid(self):
        """Situation: LABEL of entity_03 is exactly equal to UUID of entity_01

        Verify that using an ambiguous identifier gives precedence to the UUID interpretation
        Appending the special ambiguity breaker character will force the identifier to be treated as a LABEL
        """
        identifier = f'{self.entity_03.label}'
        result = self.param.convert(identifier, None, None)
        assert result.uuid == self.entity_01.uuid

        identifier = f'{self.entity_03.label}{OrmEntityLoader.label_ambiguity_breaker}'
        result = self.param.convert(identifier, None, None)
        assert result.uuid == self.entity_03.uuid
