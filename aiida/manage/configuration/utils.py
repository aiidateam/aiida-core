# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Definition of known configuration options and methods to parse and get option values."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import io
import os

from .config import Config
from .migrations import check_and_migrate_config
from .settings import DEFAULT_CONFIG_FILE_NAME

__all__ = ('load_config',)


def load_config(create=False):
    """Instantiate the Config object representing the configuration file of the current AiiDA instance.

    :param create: when set to True, will create the configuration file if it does not already exist
    :return: the config
    :rtype: :class:`~aiida.manage.configuration.config.Config`
    :raises aiida.common.MissingConfigurationError: if the configuration file could not be found and create=False
    """
    from .settings import AIIDA_CONFIG_FOLDER
    from aiida.backends.settings import IN_RT_DOC_MODE, DUMMY_CONF_FILE
    from aiida.common import exceptions
    from aiida.common import json

    if IN_RT_DOC_MODE:
        return DUMMY_CONF_FILE

    filepath = os.path.join(AIIDA_CONFIG_FOLDER, DEFAULT_CONFIG_FILE_NAME)

    if not os.path.isfile(filepath):
        if not create:
            raise exceptions.MissingConfigurationError('configuration file {} does not exist'.format(filepath))
        else:
            config = Config(filepath, {}).store()
    else:
        try:
            with io.open(filepath, 'r', encoding='utf8') as handle:
                config = Config(filepath, json.load(handle))
        except ValueError:
            raise exceptions.ConfigurationError('configuration file {} contains invalid JSON'.format(filepath))

    return check_and_migrate_config(config, store=True)
