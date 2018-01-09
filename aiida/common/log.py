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

aiidalogger = logging.getLogger('aiida')


def setup_logging(daemon=False, daemon_handler='daemon_logfile'):
    """
    Setup the logging by retrieving the LOGGING dictionary from aiida and passing it to
    the python module logging.config.dictConfig. If the logging needs to be setup for the
    daemon running a task for one of the celery workers, set the argument 'daemon' to True.
    This will cause the 'daemon_handler' to be added to all the configured loggers. This
    handler needs to be defined in the LOGGING dictionary and is 'daemon_logfile' by
    default. If this changes in the dictionary, be sure to pass the correct handle name.
    The daemon handler should be a RotatingFileHandler that writes to the daemon log file.

    :param daemon: configure the logging for a daemon task by adding a file handler instead
        of the default 'console' StreamHandler
    :param daemon_handler: name of the file handler in the LOGGING dictionary
    """
    from copy import deepcopy
    from aiida import LOGGING

    config = deepcopy(LOGGING)

    # Add the daemon file handler to all loggers if daemon=True
    if daemon is True:
        for name, logger in config.get('loggers', {}).iteritems():
            logger.setdefault('handlers', []).append(daemon_handler)

    logging.config.dictConfig(config)