# -*- coding: utf-8 -*-

from __future__ import absolute_import
from aiida import settings

STORAGE_BACKEND = getattr(settings, "STORAGE_BACKEND", "django")

from aiida.orm.implementation.general.calculation import from_type_to_pluginclassname

if STORAGE_BACKEND == "sqlalchemy":
    pass
elif STORAGE_BACKEND == "django":
    from aiida.orm.implementation.django.calculation.job import JobCalculation
    from aiida.orm.implementation.django.calculation.inline import (
        InlineCalculation, make_inline)

    from aiida.orm.implementation.general.calculation.job import _input_subfolder
