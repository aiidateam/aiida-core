# -*- coding: utf-8 -*-
from django.db import models as m

from django.core.validators import EmailValidator

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.3.0"

validate_email = EmailValidator()

class CustomEmailField(m.EmailField):
    """
    Custom Email Field using the validation backported from Django 1.7 
    to allow xxx@localhost emails.
    
    To remove once we migrate to django 1.7.
    """
    # I just replace the validator with the one taken from a more recent
    # Django release, that supports @localhost as domain. To remove
    # when we move to Django 1.7.
    default_validators = [validate_email]

