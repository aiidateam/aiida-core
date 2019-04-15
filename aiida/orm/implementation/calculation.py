# -*- coding: utf-8 -*-

from __future__ import absolute_import

from aiida.backends.settings import BACKEND
from aiida.common.exceptions import ConfigurationError

from aiida.orm.implementation.general.calculation import from_type_to_pluginclassname
from aiida.orm.implementation.general.calculation.job import _input_subfolder

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__authors__ = "The AiiDA team."
__version__ = "0.6.0.1"

if BACKEND == "sqlalchemy":
    from aiida.orm.implementation.sqlalchemy.calculation import Calculation
    from aiida.orm.implementation.sqlalchemy.calculation.job import JobCalculation
    from aiida.orm.implementation.sqlalchemy.calculation.inline import (
        InlineCalculation, make_inline)

elif BACKEND == "django":
    from aiida.orm.implementation.django.calculation import Calculation
    from aiida.orm.implementation.django.calculation.job import JobCalculation
    from aiida.orm.implementation.django.calculation.inline import (
        InlineCalculation, make_inline)

else:
    raise ConfigurationError("Invalid settings.BACKEND: {}".format(
                BACKEND))

