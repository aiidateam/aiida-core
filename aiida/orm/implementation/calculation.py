# -*- coding: utf-8 -*-

from __future__ import absolute_import
from aiida import settings

from aiida.orm.implementation.general.calculation import from_type_to_pluginclassname
from aiida.orm.implementation.general.calculation.job import _input_subfolder

if settings.BACKEND == "sqlalchemy":
    from aiida.orm.implementation.sqlalchemy.calculation.job import JobCalculation
    from aiida.orm.implementation.sqlalchemy.calculation.inline import (
        InlineCalculation, make_inline)

elif settings.BACKEND == "django":
    from aiida.orm.implementation.django.calculation.job import JobCalculation
    from aiida.orm.implementation.django.calculation.inline import (
        InlineCalculation, make_inline)

