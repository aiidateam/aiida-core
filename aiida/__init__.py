# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import logging
import warnings
from logging import config
from aiida.common.setup import get_property

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.8.0rc1"
__authors__ = "The AiiDA team."
__paper__ = """G. Pizzi, A. Cepellotti, R. Sabatini, N. Marzari, and B. Kozinsky, "AiiDA: automated interactive infrastructure and database for computational science", Comp. Mat. Sci 111, 218-230 (2016); http://dx.doi.org/10.1016/j.commatsci.2015.09.013 - http://www.aiida.net."""
__paper_short__ = """G. Pizzi et al., Comp. Mat. Sci 111, 218 (2016)."""


# Custom logging level, intended specifically for informative log messages
# reported during WorkChains and Workflows.
LOG_LEVEL_REPORT = 25
logging.addLevelName(LOG_LEVEL_REPORT, 'REPORT')

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
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
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'halfverbose',
        },
        'dblogger': {
            # get_property takes the property from the config json file
            # The key used in the json, and the default value, are
            # specified in the _property_table inside aiida.common.setup
            # NOTE: To modify properties, use the 'verdi devel setproperty'
            #   command and similar ones (getproperty, describeproperties, ...)
            'level': get_property('logging.db_loglevel'),
            'class': 'aiida.utils.logger.DBLogHandler',
        },
    },
    'loggers': {
        'aiida': {
            'handlers': ['console', 'dblogger'],
            'level': get_property('logging.aiida_loglevel'),
            'propagate': False,
        },
        'paramiko': {
            'handlers': ['console'],
            'level': get_property('logging.paramiko_loglevel'),
            'propagate': False,
        },
    },
}

# Configure the global logger through the LOGGING dictionary
logging.config.dictConfig(LOGGING)

if get_property("warnings.showdeprecations"):
    # print out the warnings coming from deprecation
    # in Python 2.7 it is suppressed by default
    warnings.simplefilter('default', DeprecationWarning)


def load_dbenv(*argc, **argv):
    """
    Alias for `load_dbenv` from `aiida.backends.utils`
    """
    from aiida.backends.utils import load_dbenv
    return load_dbenv(*argc, **argv)


def is_dbenv_loaded(*argc, **argv):
    """
    Alias for `is_dbenv_loaded` from `aiida.backends.utils`
    """
    from aiida.backends.utils import is_dbenv_loaded
    return is_dbenv_loaded(*argc, **argv)


def get_version():
    """
    Very simple function to get a string with the version number.
    """
    return __version__


def get_file_header():
    """
    Get a string to be put as header of files created with AiiDA
    """
    return """# This file has been created with AiiDA v. {}
#
# If you use AiiDA for publication purposes, please cite:
# {}
""".format(__version__, __paper__)
