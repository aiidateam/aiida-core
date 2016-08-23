# -*- coding: utf-8 -*-

from plum.wait import WaitOn, validate_callback_func
from aiida.orm.utils import load_node
from aiida.common.lang import override
from aiida.workflows2.defaults import class_loader

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


class WaitOnJobCalculation(WaitOn):
    PK = "pk"

    @classmethod
    def create_from(cls, bundle):
        return WaitOnJobCalculation(
            bundle[cls.BundleKeys.CALLBACK_NAME.value], bundle[cls.PK])

    def __init__(self, callback_name, pk):
        super(WaitOnJobCalculation, self).__init__(callback_name)
        self._pk = pk

    @override
    def is_ready(self, registry=None):
        return not load_node(pk=self._pk)._is_running()

    @override
    def save_instance_state(self, out_state):
        super(WaitOnJobCalculation, self).save_instance_state(out_state)
        out_state[self.PK] = self._pk
        out_state.set_class_loader(class_loader)


def wait_on_job_calculation(callback, pk):
    validate_callback_func(callback)
    return WaitOnJobCalculation(callback.__name__, pk)
