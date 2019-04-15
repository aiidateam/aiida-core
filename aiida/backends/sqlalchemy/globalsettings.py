# -*- coding: utf-8 -*-
"""
Functions to manage the global settings stored in the DB (in the DbSettings
table.
"""

from aiida.backends.sqlalchemy import session
from aiida.backends.sqlalchemy.models.settings import DbSetting
from sqlalchemy.orm.exc import NoResultFound

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1.1"
__authors__ = "The AiiDA team."


def set_global_setting(key, value, description=None):
    """
    Set a global setting in the DbSetting table (therefore, stored at the DB
    level).
    """
    DbSetting.set_value(key, value, other_attribs={"description": description})


def del_global_setting(key):
    """
    Return the value of the given setting, or raise a KeyError if the
    setting is not present in the DB.
    
    :raise KeyError: if the setting does not exist in the DB
    """
    try:
        setting = session.query(DbSetting).filter_by(key=key).one()
        setting.delete()
    except NoResultFound:
        raise KeyError("No global setting with key={}".format(key))


def get_global_setting(key):
    """
    Return the value of the given setting, or raise a KeyError if the
    setting is not present in the DB.
    
    :raise KeyError: if the setting does not exist in the DB
    """
    try:
        return session.query(DbSetting).filter_by(key=key).one().getvalue()
    except NoResultFound:
        raise KeyError("No global setting with key={}".format(key))


def get_global_setting_description(key):
    """
    Return the description for the given setting variable, as stored in the
    DB, or raise a KeyError if the setting is not present in the DB.
    """
    try:
        return (session.query(DbSetting).filter_by(key=key).
                one().get_description())
    except NoResultFound:
        raise KeyError("No global setting with key={}".format(key))
