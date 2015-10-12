# -*- coding: utf-8 -*-

from __future__ import absolute_import
from aiida import settings

STORAGE_BACKEND = getattr(settings, "STORAGE_BACKEND", "django")

if STORAGE_BACKEND == "sqlalchemy":
    raise NotImplemented
elif STORAGE_BACKEND == "django":
    from aiida.orm.implementation.django.calculation.job import JobCalculation, from_type_to_pluginclassname
    from aiida.orm.implementation.django.calculation.inline import (
        InlineCalculation, make_inline)

    from aiida.orm.implementation.general.calculation.job import _input_subfolder
