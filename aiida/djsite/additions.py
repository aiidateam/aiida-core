from django.db import models as m

from aiida.common.additions import CustomEmailValidator

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

