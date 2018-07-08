# -*- coding: utf-8 -*-
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
