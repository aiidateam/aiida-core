# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase
from aiida.orm.mixins import Sealable


class TestSealable(AiidaTestCase):

    def test_change_updatable_attrs_after_store(self):
        """
        Verify that a Sealable node can alter updatable attributes even after storing
        """
        from aiida.orm.calculation.job import JobCalculation

        resources = {'num_machines': 1, 'num_mpiprocs_per_machine': 1}
        job = JobCalculation(computer=self.computer, resources=resources)
        job.store()

        for attr in JobCalculation._updatable_attributes:
            if attr != Sealable.SEALED_KEY:
                job._set_attr(attr, 'a')
