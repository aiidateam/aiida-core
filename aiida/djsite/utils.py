# -*- coding: utf-8 -*-
import logging

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

def load_dbenv():    
    """
    Load the database environment (Django) and perform some checks
    """
    import os
    os.environ['DJANGO_SETTINGS_MODULE'] = 'aiida.djsite.settings.settings'
    # Check schema version and the existence of the needed tables
    check_schema_version()

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
    from aiida.common.setup import get_config, DEFAULT_USER_CONFIG_FIELD
    
    try:
        email = get_config()[DEFAULT_USER_CONFIG_FIELD]
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

def get_after_database_creation_signal():
    """
    Return the correct signal to attach to (and the sender),
    to be used when we want to perform operations
    after the AiiDA tables are created (e.g., trigger installation).
    
    This can be:
    
    * ``south.signals.post_migrate`` if this is not a test (because normally,
      tables are managed by South and are not created right after the 
      syncdb, but rather after this signal).
    * ``django.db.models.signals.post_syncdb`` if this is a test (because in 
      tests, South is not used)
          
    :return: a tuple ``(signal, sender)``, where ``signal`` is the signal to attach
        to, and ``sender`` is the sender to filter by in the ``signal.connect()``
        call.
    """
    from aiida.djsite.settings import settings
    from aiida.common.exceptions import ConfigurationError
    
    if settings.AFTER_DATABASE_CREATION_SIGNAL == 'post_syncdb':
        from django.contrib.auth import models as auth_models
        from django.db.models.signals import post_syncdb

        if 'south'  in settings.INSTALLED_APPS:
            raise ConfigurationError("AFTER_DATABASE_CREATION_SIGNAL is "
                "post_syncdb, but south is in the INSTALLED_APPS")        

        return post_syncdb,  auth_models
    elif settings.AFTER_DATABASE_CREATION_SIGNAL == 'post_migrate':
        if 'south' not in settings.INSTALLED_APPS:
            raise ConfigurationError("AFTER_DATABASE_CREATION_SIGNAL is "
                "post_migrate, but south is not in the INSTALLED_APPS")
                    
        from south.signals import post_migrate
        return post_migrate, None # No sender is needed for this model
    else:
        raise ConfigurationError(
            "The settings.AFTER_DATABASE_CREATION_SIGNAL has an invalid value")

def long_field_length():
    """
    Return the length of "long" fields.
    This is used, for instance, for the 'key' field of attributes.
    This returns 1024 typically, but it returns 255 if the backend is mysql.
    """
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
      syncdb call.
      
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
                                 "table) is {}, I stop.".format(
                                    code_schema_version, db_schema_version))
    
    