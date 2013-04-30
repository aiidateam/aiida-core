import getpass

from django.core.exceptions import ObjectDoesNotExist
from aida.common.exceptions import ConfigurationError

from django.contrib.auth.models import User

def get_automatic_user(username=getpass.getuser()):
    try:
        return User.objects.get(username=username)
    except ObjectDoesNotExist:
        raise ConfigurationError("No aida user with username {}".format(
                username))

