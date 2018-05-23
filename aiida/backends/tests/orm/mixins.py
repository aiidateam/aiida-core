# -*- coding: utf-8 -*-
from aiida.backends.testbase import AiidaTestCase


class TestSealable(AiidaTestCase):

    def test_copy_not_include_updatable_attrs(self):
    	"""
    	Verify that a node with an updatable attribute, e.g. 'sealed' from the
    	Sealable mixin, can be copied successfully
    	"""
    	from aiida.orm.calculation.job import JobCalculation

    	job = JobCalculation()
    	job.seal()
    	job.copy(include_updatable_attrs=False)
