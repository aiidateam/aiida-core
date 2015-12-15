# -*- coding: utf-8 -*-
from django.db import models as m

from aiida.common.additions import CustomEmailValidator

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Eric Hontz, Giovanni Pizzi, Martin Uhrin"

custom_validate_email = CustomEmailValidator()


class CustomEmailField(m.EmailField):
    """
    Custom Email Field using the validation backported from Django 1.7 
    to allow xxx@localhost emails.
    
    To remove once we migrate to django 1.7.
    """
    # I just replace the validator with the one taken from a more recent
    # Django release, that supports @localhost as domain. To remove
    # when we move to Django 1.7.
    default_validators = [custom_validate_email]

