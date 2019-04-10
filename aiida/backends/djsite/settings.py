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
Django settings for the AiiDA project.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import sys
import os

from aiida.common import exceptions
from aiida.common.timezone import get_current_timezone
from aiida.manage.configuration import get_profile, settings

# Assumes that parent directory of aiida is root for
# things like templates/, SQL/ etc.  If not, change what follows...

AIIDA_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.split(AIIDA_DIR)[0]
sys.path = [BASE_DIR] + sys.path

try:
    PROFILE = get_profile()
except exceptions.MissingConfigurationError as exception:
    raise exceptions.MissingConfigurationError('the configuration could not be loaded: {}'.format(exception))

if PROFILE is None:
    raise exceptions.ProfileConfigurationError('no profile has been loaded')

if PROFILE.database_backend != 'django':
    raise exceptions.ProfileConfigurationError('incommensurate database backend `{}` for profile `{}`'.format(
        PROFILE.database_backend, PROFILE.name))

PROFILE_CONF = PROFILE.dictionary

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.' + PROFILE.database_engine,
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

# Local time zone for this installation. Always choose the system timezone
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
                'django.contrib.auth.context_processors.auth',
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
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'aiida.backends.djsite.db',
]
