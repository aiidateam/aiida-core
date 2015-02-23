# -*- coding: utf-8 -*-
import logging

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.3.0"

def load_dbenv(process=None,profile=None):
    """
    Load the database environment (Django) and perform some checks
    """
    _load_dbenv_noschemacheck(process,profile)
    # Check schema version and the existence of the needed tables
    check_schema_version()


def _load_dbenv_noschemacheck(process,profile=None):
    """
    Load the database environment (Django) WITHOUT CHECKING THE SCHEMA VERSION.
    
    :param process: ...
    
    This should ONLY be used internally, inside load_dbenv, and for schema 
    migrations. DO NOT USE OTHERWISE!
    """
    import os
    import django
    from aiida.common.setup import get_default_profile,DEFAULT_PROCESS
    from aiida.djsite.settings import settings_profile
    
    if profile is not None and process is not None:
        raise TypeError("You have to pass either process or profile to "
                         "load_dbenv_noschemacheck")
    if profile is not None:
        settings_profile.AIIDADB_PROFILE = profile
        settings_profile.CURRENT_AIIDADB_PROCESS = None
    else:
        actual_process = process if process is not None else DEFAULT_PROCESS
        settings_profile.AIIDADB_PROFILE = get_default_profile(actual_process)
        settings_profile.CURRENT_AIIDADB_PROCESS = actual_process
        
    os.environ['DJANGO_SETTINGS_MODULE'] = 'aiida.djsite.settings.settings'
    django.setup()
    
class DBLogHandler(logging.Handler):
    def emit(self, record):
        from django.core.exceptions import ImproperlyConfigured 
        try:
            from aiida.djsite.db.models import DbLog
            
            DbLog.add_from_logrecord(record)
            
        except ImproperlyConfigured:
            # Probably, the logger was called without the
            # Django settings module loaded. Then,
            # This ignore should be a no-op.
            pass
        except Exception:
            # To avoid loops with the error handler, I just print.
            # Hopefully, though, this should not happen!
            import traceback
            traceback.print_exc() 

def get_dblogger_extra(obj):
    """
    Given an object (Node, Calculation, ...) return a dictionary to be passed
    as extra to the aiidalogger in order to store the exception also in the DB.
    If no such extra is passed, the exception is only logged on file.
    """
    from aiida.orm import Node
    
    if isinstance(obj, Node):
        if obj._plugin_type_string:
            objname = "node." + obj._plugin_type_string
        else:
            objname = "node"
    else:
        objname = obj.__class__.__module__ + "." + obj.__class__.__name__
    objpk = obj.pk
    return {'objpk': objpk, 'objname': objname}

def get_log_messages(obj):
    from aiida.djsite.db.models import DbLog
    import json
    
    extra = get_dblogger_extra(obj)
    # convert to list, too
    log_messages = list(DbLog.objects.filter(**extra).order_by('time').values(
        'loggername', 'levelname', 'message', 'metadata', 'time'))

    #  deserialize metadata
    for log in log_messages:
        log.update({'metadata': json.loads(log['metadata'])})

    return log_messages

def get_configured_user_email():
    """
    Return the email (that is used as the username) configured during the 
    first verdi install.
    """
    from aiida.common.exceptions import ConfigurationError
    from aiida.common.setup import get_profile_config, DEFAULT_USER_CONFIG_FIELD
    from aiida.djsite.settings import settings_profile 
    
    try:
        profile_conf = get_profile_config(settings_profile.AIIDADB_PROFILE)
        email = profile_conf[DEFAULT_USER_CONFIG_FIELD]
    # I do not catch the error in case of missing configuration, because
    # it is already a ConfigurationError
    except KeyError:
        raise ConfigurationError("No 'default_user' key found in the "
            "AiiDA configuration file".format(DEFAULT_USER_CONFIG_FIELD))
    return email

def get_daemon_user():
    """
    Return the username (email) of the user that should run the daemon,
    or the default AiiDA user in case no explicit configuration is found
    in the DbSetting table.
    """
    from aiida.common.globalsettings import get_global_setting
    from aiida.common.setup import DEFAULT_AIIDA_USER
    
    try: 
        return get_global_setting('daemon|user')
    except KeyError:
        return DEFAULT_AIIDA_USER

def set_daemon_user(user_email):
    """
    Set the username (email) of the user that is allowed to run the daemon.
    """
    from aiida.common.globalsettings import set_global_setting
    
    set_global_setting('daemon|user', user_email,
                       description="The only user that is allowed to run the "
                                    "AiiDA daemon on this DB instance")

_aiida_autouser_cache = None
    
def get_automatic_user():
    """
    Return the default user for this installation of AiiDA.
    """
    global _aiida_autouser_cache
    
    if _aiida_autouser_cache is not None:
        return _aiida_autouser_cache

    from django.core.exceptions import ObjectDoesNotExist
    from aiida.djsite.db.models import DbUser
    from aiida.common.exceptions import ConfigurationError

    email = get_configured_user_email()
        
    try:
        _aiida_autouser_cache = DbUser.objects.get(email=email)
        return _aiida_autouser_cache
    except ObjectDoesNotExist:
        raise ConfigurationError("No aiida user with email {}".format(
                email))

def long_field_length():
    """
    Return the length of "long" fields.
    This is used, for instance, for the 'key' field of attributes.
    This returns 1024 typically, but it returns 255 if the backend is mysql.
    
    :note: Call this function only AFTER having called load_dbenv!
    """
    # One should not load directly settings because there are checks inside 
    # for the current profile. However, this function is going to be called
    # only after having loaded load_dbenv, so there should be no problem
    from aiida.djsite.settings import settings
    if 'mysql' in settings.DATABASES['default']['ENGINE']:
        return 255
    else:
        return 1024

def get_db_schema_version():
    """
    Get the current schema version stored in the DB. Return None if
    it is not stored.
    """
    from aiida.common.globalsettings import get_global_setting
    
    try:
        return get_global_setting('db|schemaversion')
    except KeyError:
        return None

def set_db_schema_version(version):
    """
    Set the schema version stored in the DB. Use only if you know what
    you are doing.
    """
    from aiida.common.globalsettings import set_global_setting
    
    return set_global_setting('db|schemaversion', version, description=
                              "The version of the schema used in this "
                              "database.")

def check_schema_version():
    """
    Check if the version stored in the database is the same of the version
    of the code.
    
    :note: if the DbSetting table does not exist, this function does not
      fail. The reason is to avoid to have problems before running the first
      migrate call.
      
    :note: if no version is found, the version is set to the version of the
      code. This is useful to have the code automatically set the DB version
      at the first code execution.
    
    :raise ConfigurationError: if the two schema versions do not match.
      Otherwise, just return.
    """
    import aiida.djsite.db.models
    from django.db import connection
    from aiida.common.exceptions import ConfigurationError

    # Do not do anything if the table does not exist yet
    if 'db_dbsetting' not in connection.introspection.table_names():
        return
    
    code_schema_version = aiida.djsite.db.models.SCHEMA_VERSION
    db_schema_version = get_db_schema_version()
    
    if db_schema_version is None:
        # No code schema defined yet, I set it to the code version
        set_db_schema_version(code_schema_version)
        db_schema_version = get_db_schema_version()
    
    if code_schema_version != db_schema_version:
        raise ConfigurationError("The code schema version is {}, but the "
            "version stored in the database (DbSetting "
            "table) is {}, I stop [migrate using tools in "
            "aiida/djsite/aiida_migrations]".format(
                                    code_schema_version, db_schema_version))
    
    
