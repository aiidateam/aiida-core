# -*- coding: utf-8 -*-
"""
Classes needed for tests.
Must be here because subclasses of 'Node' must be within aiida.orm
"""
from aiida.orm.calculation import Calculation



class myNodeWithFields(Calculation):
    # State can be updated even after storing
    _updatable_attributes = ('state',)
