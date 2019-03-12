# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for logging methods/classes that need the ORM."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import logging


class DBLogHandler(logging.Handler):
    """A custom db log handler for writing logs tot he database"""

    def emit(self, record):
        # If this is reached before a backend is defined, simply pass
        from aiida.backends.utils import is_dbenv_loaded
        if not is_dbenv_loaded():
            return

        if record.exc_info:
            # We do this because if there is exc_info this will put an appropriate string in exc_text.
            # See:
            # https://github.com/python/cpython/blob/1c2cb516e49ceb56f76e90645e67e8df4e5df01a/Lib/logging/handlers.py#L590
            self.format(record)

        from aiida import orm
        from django.core.exceptions import ImproperlyConfigured  # pylint: disable=no-name-in-module, import-error

        try:
            try:
                backend = record.__dict__.pop('backend')
                orm.Log.objects(backend).create_entry_from_record(record)
            except KeyError:
                # The backend should be set. We silently absorb this error
                pass

        except ImproperlyConfigured:
            # Probably, the logger was called without the
            # Django settings module loaded. Then,
            # This ignore should be a no-op.
            pass
        except Exception:  # pylint: disable=broad-except
            # To avoid loops with the error handler, I just print.
            # Hopefully, though, this should not happen!
            import traceback
            traceback.print_exc()
            raise


def get_dblogger_extra(node):
    """Return the additional information necessary to attach any log records to the given node instance.

    :param node: a Node instance
    """
    from aiida.orm import Node

    # If the object is not a Node or it is not stored, then any associated log records should bot be stored. This is
    # accomplished by returning an empty dictionary because the `dbnode_id` is required to successfully store it.
    if not isinstance(node, Node) or not node.is_stored:
        return dict()

    return {'dbnode_id': node.id, 'backend': node.backend}


def create_logger_adapter(logger, node):
    """Create a logger adapter for the given Node instance.

    :param logger: the logger to adapt
    :param node: the node instance to create the adapter for
    :return: the logger adapter
    :rtype: :class:`logging.LoggerAdapter`
    """
    from aiida.orm import Node

    if not isinstance(node, Node):
        raise TypeError('node should be an instance of `Node`')

    return logging.LoggerAdapter(logger=logger, extra=get_dblogger_extra(node))
