# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# Django settings for the AiiDA project.
import sys
import os

from aiida.common.exceptions import ConfigurationError

# get_property is used to read properties stored in the config json
from aiida.common.setup import (get_config, get_secret_key, get_property,
                                get_profile_config, parse_repository_uri)
from aiida.backends import settings
from aiida.utils.timezone import get_current_timezone

# Assumes that parent directory of aiida is root for
# things like templates/, SQL/ etc.  If not, change what follows...


AIIDA_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.split(AIIDA_DIR)[0]
sys.path = [BASE_DIR] + sys.path

try:
    confs = get_config()
except ConfigurationError:
    raise ConfigurationError(
        "Please run the AiiDA Installation, no config found")

if settings.AIIDADB_PROFILE is None:
    raise ConfigurationError(
        "settings.AIIDADB_PROFILE not defined, did you load django"
        "through the AiiDA load_dbenv()?")

profile_conf = get_profile_config(settings.AIIDADB_PROFILE, conf_dict=confs)

# put all database specific portions of settings here
DBENGINE = profile_conf.get('AIIDADB_ENGINE', '')
DBNAME = profile_conf.get('AIIDADB_NAME', '')
DBUSER = profile_conf.get('AIIDADB_USER', '')
DBPASS = profile_conf.get('AIIDADB_PASS', '')
DBHOST = profile_conf.get('AIIDADB_HOST', '')
DBPORT = profile_conf.get('AIIDADB_PORT', '')
REPOSITORY_URI = profile_conf.get('AIIDADB_REPOSITORY_URI', '')

DATABASES = {
    'default': {
        # Add 'postgresql_psycopg2', 'mysql', or 'oracle'.
        'ENGINE': 'django.db.backends.' + DBENGINE,
        'NAME': DBNAME,
        'USER': DBUSER,
        'PASSWORD': DBPASS,
        'HOST': DBHOST,
        'PORT': DBPORT,
    }
}

# Checks on the REPOSITORY_* variables
try:
    REPOSITORY_URI
except NameError:
    raise ConfigurationError(
        "Please setup correctly the REPOSITORY_URI variable to "
        "a suitable directory on which you have write permissions.")

# Note: this variable might disappear in the future
REPOSITORY_PROTOCOL, REPOSITORY_PATH = parse_repository_uri(REPOSITORY_URI)

if settings.IN_DOC_MODE:
    pass
elif REPOSITORY_PROTOCOL == 'file':
    if not os.path.isdir(REPOSITORY_PATH):
        try:
            # Try to create the local repository folders with needed parent
            # folders
            os.makedirs(REPOSITORY_PATH)
        except OSError:
            # Possibly here due to permission problems
            raise ConfigurationError(
                "Please setup correctly the REPOSITORY_PATH variable to "
                "a suitable directory on which you have write permissions. "
                "(I was not able to create the directory.)")
else:
    raise ConfigurationError("Only file protocol supported")

# CUSTOM USER CLASS
AUTH_USER_MODEL = 'db.DbUser'

# Make this unique, and don't share it with anybody.
# This is generated with the first run of 'verdi install'
SECRET_KEY = get_secret_key()

# Usual Django settings starts here.............

# Keep it to False! Otherwise every query is stored
# in memory and looks like a memory leak with celery
DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# Local time zone for this installation. Always choose the system timezone
TIME_ZONE = get_current_timezone().zone

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = False

# If you set this to False, Django will not use timezone-aware datetimes.
# For AiiDA, leave it as True, otherwise setting properties with dates will not work.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''
# MEDIA_ROOT = '%s/templates/' % BASE_DIR

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = None

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'aiida.backends.djsite.settings.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'aiida.backends.djsite.settings.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
)

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'aiida.backends.djsite.db',
]
try:
    import kombu
    INSTALLED_APPS.append('kombu.transport.django')
except ImportError:
    pass

# Automatic logging configuration for Django is disabled here
# and done for all backends in aiida/__init__.py
LOGGING_CONFIG = None

# -------------------------
# Tastypie (API) settings
# -------------------------
# For the time being, we support only json
TASTYPIE_DEFAULT_FORMATS = ['json']

