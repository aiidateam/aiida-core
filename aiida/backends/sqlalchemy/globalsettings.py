# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Functions to manage the global settings stored in the DB (in the DbSettings
table.
"""

from aiida.backends.sqlalchemy.models.settings import DbSetting
from sqlalchemy.orm.exc import NoResultFound
from aiida.backends.sqlalchemy import get_scoped_session


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
        setting = get_scoped_session().query(DbSetting).filter_by(key=key).one()
        setting.delete()
    except NoResultFound:
        raise KeyError("No global setting with key={}".format(key))


def get_global_setting(key):
    """
    Return the value of the given setting, or raise a KeyError if the
    setting is not present in the DB.
    
    :raise KeyError: if the setting does not exist in the DB
    """
    from aiida.backends.sqlalchemy.models.utils import get_value_of_sub_field

    # Check first that the table exists
    table_check_test()

    try:
        return get_value_of_sub_field(
            key, lambda given_key: get_scoped_session().query(DbSetting).filter_by(
                key=given_key).one().getvalue())
    except NoResultFound:
        raise KeyError("No global setting with key={}".format(key))


def get_global_setting_description(key):
    """
    Return the description for the given setting variable, as stored in the
    DB, or raise a KeyError if the setting is not present in the DB or the
    table doesn't exist.
    """
    from aiida.backends.sqlalchemy.models.utils import validate_key

    # Check first that the table exists
    table_check_test()
    validate_key(key)

    try:
        return (get_scoped_session().query(DbSetting).filter_by(key=key).
                one().get_description())
    except NoResultFound:
        raise KeyError("No global setting with key={}".format(key))


def table_check_test():
    """
    Checks if the db_setting table exists in the database. If it doesn't exist
    it rainses a KeyError.
    """
    from sqlalchemy.engine import reflection
    from aiida.backends import sqlalchemy as sa
    inspector = reflection.Inspector.from_engine(get_scoped_session().bind)
    if 'db_dbsetting' not in inspector.get_table_names():
        raise KeyError("No table found")

