# -*- coding: utf-8 -*-
# Django settings for the AiiDA project.
import sys, os
from aiida.common.exceptions import ConfigurationError
from aiida.common.setup import get_config, get_secret_key

# Assumes that parent directory of aiida is root for
# things like templates/, SQL/ etc.  If not, change what follows...

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

AIIDA_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.split(AIIDA_DIR)[0]
sys.path = [BASE_DIR] + sys.path

try:
    confs = get_config()
except ConfigurationError:
    raise ConfigurationError("Please run the AiiDA Installation")
          
#put all database specific portions of settings here
DBENGINE = confs.get('AIIDADB_ENGINE', '')
DBNAME = confs.get('AIIDADB_NAME', '')
DBUSER = confs.get('AIIDADB_USER', '')
DBPASS = confs.get('AIIDADB_PASS', '')
DBHOST = confs.get('AIIDADB_HOST', '')
DBPORT = confs.get('AIIDADB_PORT', '')
LOCAL_REPOSITORY = confs.get('AIIDADB_REPOSITORY', '')

DATABASES = {
    'default' : {
        # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'. 
        'ENGINE'    : 'django.db.backends.' + DBENGINE, 
        'NAME'      : DBNAME,  # Or path to database file if using sqlite3.   
        'USER'      : DBUSER,  # Not used with sqlite3.
        'PASSWORD'  : DBPASS,  # Not used with sqlite3.
        'HOST'      : DBHOST,  # Set to empty string for localhost. Not used with sqlite3. 
        'PORT'      : DBPORT,  # Set to empty string for default. Not used with sqlite3.      
        }
    }

# Increase timeout for SQLite engine
# Does not solve the problem, but alleviates it for small number of calculations
if 'sqlite' in DBENGINE:
    DATABASES['default']['OPTIONS'] = {'timeout': 60}

## Checks on the LOCAL_REPOSITORY
try:
    LOCAL_REPOSITORY
except NameError:
    raise ConfigurationError(
        "Please setup correctly the LOCAL_REPOSITORY variable to "
        "a suitable directory on which you have write permissions.")
    
# Normalize LOCAL_REPOSITORY to its absolute path
LOCAL_REPOSITORY=os.path.abspath(LOCAL_REPOSITORY)
if not os.path.isdir(LOCAL_REPOSITORY):
    try:
        # Try to create the local repository folders with needed parent
        # folders
        os.makedirs(LOCAL_REPOSITORY)
    except OSError:
        # Possibly here due to permission problems
        raise ConfigurationError(
            "Please setup correctly the LOCAL_REPOSITORY variable to "
            "a suitable directory on which you have write permissions. "
            "(I was not able to create the directory.)")

# CUSTOM USER CLASS
AUTH_USER_MODEL = 'db.DbUser'

# Make this unique, and don't share it with anybody.
# This is generated with the first run of 'verdi install'
SECRET_KEY = get_secret_key()
        
# Usual Django settings starts here.............

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
try:
    TIME_ZONE = confs['TIMEZONE']
except KeyError:
    raise ConfigurationError("You did not set your timezone during the "
                             "verdi install phase.")

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
#MEDIA_ROOT = '%s/templates/' % BASE_DIR

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

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
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'aiida.djsite.settings.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'aiida.djsite.settings.wsgi.application'

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

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
#    'south',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'aiida.djsite.db',
    'kombu.transport.django',
    'djcelery',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
#
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d '
                      '%(thread)d %(message)s',
            },
        'halfverbose': {
            'format': '%(asctime)s, %(name)s: [%(levelname)s] %(message)s',
            'datefmt': '%m/%d/%Y %I:%M:%S %p',
            },
        },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
            }
        },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'halfverbose',
        },
        'dblogger': {
            'level': 'WARNING',
            'class': 'aiida.djsite.utils.DBLogHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'aiida': {
            'handlers': ['console', 'dblogger'],
            'level': 'WARNING',
            'propagate': False,
            },
        'celery': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
            },
        'paramiko': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
            },
        },
}

# We don't need to run the South migrations every time we want to run the
# test suite. This leads to massive speedup.
# However, we have to remember to attach operations that expect the tables
# to be created (as the creation of the triggers) either to:
# - south->post_migrate if this is not a test
# - django->post_syncdb if this is a test (this is set in
#     cmdline.commands.verdilib.DeveloperTest.run)
SOUTH_TESTS_MIGRATE = False
# This is only a string: call
# aiida.djsite.utils.get_after_database_creation_signal
# to get the proper signal
# Uncomment next line if using south
#AFTER_DATABASE_CREATION_SIGNAL = 'post_migrate'
AFTER_DATABASE_CREATION_SIGNAL = 'post_syncdb'

# VERSION TO USE FOR DBNODES.
AIIDANODES_UUID_VERSION=4

# -------------------------
# Tastypie (API) settings
# -------------------------
# For the time being, we support only json
TASTYPIE_DEFAULT_FORMATS = ['json']

# -------------------------
# AiiDA-Deamon configuration
# -------------------------
#from celery.schedules import crontab
from datetime import timedelta
import djcelery

djcelery.setup_loader()

BROKER_URL = "django://"
CELERY_RESULT_BACKEND = "database"
# Avoid to store the results in the database, it uses a lot of resources
# and we do not need results
CELERY_IGNORE_RESULT=True
#CELERY_STORE_ERRORS_EVEN_IF_IGNORED=True
#CELERYD_HIJACK_ROOT_LOGGER = False

CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"

# Used internally, in the functions that get the last daemon timestamp.
# Key: internal name, left: actual celery name. Can be the same
djcelery_tasks = {
    'submitter': 'submitter',
    'updater':   'updater',
    'retriever': 'retriever',
    'workflow':  'workflow_stepper',
    }

# Choose here how often the tasks should be run. Note that if the previous task
# is still running, the new one does not start thanks to the DbLock feature 
# that we added.
CELERYBEAT_SCHEDULE = {
    djcelery_tasks['submitter']: {
        'task':'aiida.djsite.db.tasks.submitter',
        'schedule': timedelta(seconds=30),
        },
    djcelery_tasks['updater']: {
        'task':'aiida.djsite.db.tasks.updater',
        'schedule': timedelta(seconds=30),
        },
    djcelery_tasks['retriever']: {
        'task':'aiida.djsite.db.tasks.retriever',
        'schedule': timedelta(seconds=30),
        },
   djcelery_tasks['workflow']: {
        'task':'aiida.djsite.db.tasks.workflow_stepper',
        'schedule': timedelta(seconds=5),
        },
}
