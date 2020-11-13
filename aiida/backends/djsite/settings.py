# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error, no-name-in-module
""" Django settings for the AiiDA project. """
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID

from aiida.common import exceptions
from aiida.common.timezone import get_current_timezone
from aiida.manage.configuration import get_profile, settings

try:
    PROFILE = get_profile()
except exceptions.MissingConfigurationError as exception:
    raise exceptions.MissingConfigurationError(f'the configuration could not be loaded: {exception}')

if PROFILE is None:
    raise exceptions.ProfileConfigurationError('no profile has been loaded')

if PROFILE.database_backend != 'django':
    raise exceptions.ProfileConfigurationError(
        f'incommensurate database backend `{PROFILE.database_backend}` for profile `{PROFILE.name}`'
    )

PROFILE_CONF = PROFILE.dictionary

DATABASES = {
    'default': {
        'ENGINE': f'django.db.backends.{PROFILE.database_engine}',
        'NAME': PROFILE.database_name,
        'PORT': PROFILE.database_port,
        'HOST': PROFILE.database_hostname,
        'USER': PROFILE.database_username,
        'PASSWORD': PROFILE.database_password,
    }
}

# CUSTOM USER CLASS
AUTH_USER_MODEL = 'db.DbUser'

# No secret key defined since we do not use Django to serve HTTP pages
SECRET_KEY = 'placeholder'  # noqa

# Automatic logging configuration for Django is disabled here
# and done for all backends in aiida/__init__.py
LOGGING_CONFIG = None

# Keep DEBUG = False! Otherwise every query is stored in memory
DEBUG = False

ADMINS = []
ALLOWED_HOSTS = []

MANAGERS = ADMINS

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# Local time zone for this installation. Always choose the system timezone.
# Note: This causes django to set the 'TZ' environment variable, which is read by tzlocal from then onwards.
# See https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-TIME_ZONE
TIME_ZONE = get_current_timezone().zone

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = False

# If you set this to False, Django will not use timezone-aware datetimes.
# For AiiDA, leave it as True, otherwise setting properties with dates will not work.
USE_TZ = settings.USE_TZ

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug':
            DEBUG,
        },
    },
]

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'aiida.backends.djsite.db',
    'aldjemy',
]

ALDJEMY_DATA_TYPES = {
    'UUIDField': lambda field: UUID(),
    'JSONField': lambda field: JSONB(),
}
