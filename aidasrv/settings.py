# Django settings for aidasrv project.

import sys, os, os.path
from django.core.exceptions import ImproperlyConfigured

# Assumes that parent directory of aida is root for
# things like templates/, SQL/ etc.  If not, change what follows...
AIDA_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.split(AIDA_DIR)[0]
sys.path = [BASE_DIR] + sys.path

#put all database specific portions of settings here
DBENGINE = os.environ.get('AIDADB_ENGINE', '')
DBNAME = os.environ.get('AIDADB_NAME', '')
DBUSER = os.environ.get('AIDADB_USER', '')
DBPASS = os.environ.get('AIDADB_PASS', '')
DBHOST = os.environ.get('AIDADB_HOST', '')
DBPORT = os.environ.get('AIDADB_PORT', '')
LOCAL_REPOSITORY = os.environ.get('AIDADB_REPOSITORY', '')

DATABASES = {
    'default' : {
        'ENGINE'    : 'django.db.backends.' + DBENGINE,   # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'. 
        'NAME'      : DBNAME,                       # Or path to database file if using sqlite3.   
        'USER'      : DBUSER,                       # Not used with sqlite3.
        'PASSWORD'  : DBPASS,                        # Not used with sqlite3.
        'HOST'      : DBHOST,                       # Set to empty string for localhost. Not used with sqlite3. 
        'PORT'      : DBPORT,                       # Set to empty string for default. Not used with sqlite3.      
        }
    }

## Setup a sqlite3 DB for tests (WAY faster, since it remains in-memory
## and not on disk.
if 'test' in sys.argv:
    DATABASES['default'] = {'ENGINE': 'django.db.backends.sqlite3'}
    ##############################################################
    # IMPORTANT! Choose a different repository location, otherwise 
    # real data will be destroyed during tests!!
    LOCAL_REPOSITORY = '/tmp/aida_repository_test/'
    ##############################################################

## Checks on the LOCAL_REPOSITORY
if not LOCAL_REPOSITORY:
    ## Empty string
    raise ImproperlyConfigured(
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
        raise ImproperlyConfigured(
            "Please setup correctly the LOCAL_REPOSITORY variable to "
            "a suitable directory on which you have write permissions. "
            "(I was not able to create the directory.)")
        


## ========== NOTE =========
## Later on, it may be probably better to make a different settings.py for 
## testing, and then run it using
## python manage.py test --settings=aidasrv.test_settings
## to avoid that subtle bugs that are backend-dependent are not trapped

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
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
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

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'm6=!mrb!aooja+&amp;whx^f$^(r$nd6cchq6n)yg^l)tz6l)x5xx$'

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

ROOT_URLCONF = 'aidasrv.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'aidasrv.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
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
    'south',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'aidadb'
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
#
# Added logging on console for >=DEBUG signals from aidasrv module
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
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'aidasrv': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
            },
        },
}

# We don't need to run the South migrations every time we want to run the
# test suite. This leads to massive speedup.
SOUTH_TESTS_MIGRATE = False
