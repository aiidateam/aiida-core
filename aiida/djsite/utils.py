import logging

def get_last_daemon_run(task):
    """
    Return the time the given task was run the last time.
    
    :note: for the moment, it does not seem to return the exact time, but only
       an approximate time. It can be improved, but it is already sufficient to
       give the user an idea on whether the daemon is running or not.
    
    :param task: a valid task name; they are listed in the
      aiida.djsite.settings.settings.djcelery_tasks dictionary.
      
    :return: a datetime object if the task is found, or None if the task
      never run yet.
    
    :raises: Django 
    """
    from djcelery.models import PeriodicTask#, TaskMeta
    
    task = PeriodicTask.objects.get(name=task)
    last_run_at = task.last_run_at
    
    #print (TaskMeta.objects.all().order_by('-date_done')[0].date_done)
    #id = str(type(TaskMeta.objects.all().order_by('-date_done')[0].task_id))
    return last_run_at

# Cache for speed-up
_aiida_autouser_cache = None

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
        
def get_automatic_user():
    global _aiida_autouser_cache
    
    if _aiida_autouser_cache is not None:
        return _aiida_autouser_cache

    import getpass
    username = getpass.getuser()
    
    from django.contrib.auth.models import User
    from django.core.exceptions import ObjectDoesNotExist
    from aiida.common.exceptions import ConfigurationError

    try:
        _aiida_autouser_cache = User.objects.get(username=username)
        return _aiida_autouser_cache
    except ObjectDoesNotExist:
        raise ConfigurationError("No aiida user with username {}".format(
                username))

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
