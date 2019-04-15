# -*- coding: utf-8 -*-
"""
Functions to manage the global settings stored in the DB (in the DbSettings
table.
"""

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0.1"
__authors__ = "The AiiDA team."


def set_global_setting(key, value, description=None):
    """
    Set a global setting in the DbSetting table (therefore, stored at the DB
    level).
    """
    from aiida.backends.djsite.db.models import DbSetting

    # Before storing, validate the key
    DbSetting.validate_key(key)

    # This also saves in the DB    
    DbSetting.set_value(key, value,
                        other_attribs={"description": description})


def del_global_setting(key):
    """
    Return the value of the given setting, or raise a KeyError if the
    setting is not present in the DB.
    
    :raise KeyError: if the setting does not exist in the DB
    """
    from aiida.backends.djsite.db.models import DbSetting
    from django.core.exceptions import ObjectDoesNotExist

    try:
        setting = DbSetting.objects.get(key=key)
    except ObjectDoesNotExist:
        raise KeyError("No global setting with key={}".format(key))

    # This does not raise exceptions
    DbSetting.del_value(key=key)


def get_global_setting(key):
    """
    Return the value of the given setting, or raise a KeyError if the
    setting is not present in the DB.
    
    :raise KeyError: if the setting does not exist in the DB
    """
    from aiida.backends.djsite.db.models import DbSetting
    from django.core.exceptions import ObjectDoesNotExist

    try:
        return DbSetting.objects.get(key=key).getvalue()
    except ObjectDoesNotExist:
        raise KeyError("No global setting with key={}".format(key))


def get_global_setting_description(key):
    """
    Return the description for the given setting variable, as stored in the
    DB, or raise a KeyError if the setting is not present in the DB.
    """
    from aiida.backends.djsite.db.models import DbSetting
    from django.core.exceptions import ObjectDoesNotExist

    try:
        return DbSetting.objects.get(key=key).description
    except ObjectDoesNotExist:
        raise KeyError("No global setting with key={}".format(key))
