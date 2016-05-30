# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."

from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from unittest import TestCase
from aiida.workflows2.fragmented_wf2 import *


class _Wf(FragmentedWorkfunction2):
    @classmethod
    def _define(cls, spec):
        spec.outline(
            cls.s1,
            if_(cls.cond1)(
                cls.s2
            ).elif_(cls.cond2)(
                cls.s3
            ).else_(
                cls.s4
            ),
            cls.s5,
            while_(cls.cond3)(
                cls.s6
            )
        )

    def s1(self, scope):
        pass

    def s2(self, scope):
        pass

    def s3(self, scope):
        pass

    def s4(self, scope):
        pass

    def s5(self, scope):
        pass

    def s6(self, scope):
        pass

    def cond1(self, scope):
        return False

    def cond2(self, scope):
        return False

    def cond3(self, scope):
        return False


class TestFragmentedWorkfunction2(TestCase):
    def test__run(self):
        wf = _Wf()
        wf.run()
