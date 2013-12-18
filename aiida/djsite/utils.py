import getpass

from django.core.exceptions import ObjectDoesNotExist
from aiida.common.exceptions import ConfigurationError

from django.contrib.auth.models import User

def get_automatic_user(username=getpass.getuser()):
    try:
        return User.objects.get(username=username)
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
    
    if settings.AFTER_DATABASE_CREATION_SIGNAL == 'post_syncdb':
        from django.contrib.auth import models as auth_models
        from django.db.models.signals import post_syncdb
        return post_syncdb,  auth_models
    elif settings.AFTER_DATABASE_CREATION_SIGNAL == 'post_migrate':        
        from south.signals import post_migrate
        return post_migrate, None # No sender is needed for this model
    else:
        raise ConfigurationError(
            "The settings.AFTER_DATABASE_CREATION_SIGNAL has an invalid value")
