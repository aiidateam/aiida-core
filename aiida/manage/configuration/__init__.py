# -*- coding: utf-8 -*-
# pylint: disable=undefined-variable,wildcard-import,global-statement
"""Modules related to the configuration of an AiiDA instance."""

from .config import *
from .profile import *
from .utils import *

CONFIG = None

__all__ = (config.__all__ + profile.__all__ + utils.__all__ + ('get_config',))


def get_config():
    """Return the current configuration.

    If the configuration has not been loaded yet, it will be loaded first and then returned.

    Note: this function should only be called by parts of the code that expect that a complete AiiDA instance exists,
    i.e. an AiiDA folder exists and contains a valid configuration file.

    :return: the config
    :rtype: :class:`~aiida.manage.configuration.config.Config`
    :raises ConfigurationError: if the configuration file could not be found, read or deserialized
    """
    global CONFIG

    if not CONFIG:
        CONFIG = load_config()

    return CONFIG
