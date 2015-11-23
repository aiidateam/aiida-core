# -*- coding: utf-8 -*-

from __future__ import absolute_import

from aiida.backends import settings

if settings.BACKEND is None:
    from aiida.backends.profile import load_profile
    # XXX add a print statement maybe ?
    load_profile()

if settings.BACKEND == "sqlalchemy":
    from aiida.backends.sqlalchemy.utils import get_automatic_user, load_dbenv
elif settings.BACKEND == "django":
    from aiida.backends.djsite.utils import get_automatic_user, load_dbenv
    from aiida.backends.djsite.cmdline import (
        get_group_list, get_workflow_list, get_log_messages
    )
