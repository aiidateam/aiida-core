# -*- coding: utf-8 -*-

from __future__ import absolute_import

from aiida.backends.settings import BACKEND

if BACKEND == "sqlalchemy":
    from aiida.backends.sqlalchemy.utils import get_automatic_user
elif BACKEND == "django":
    from aiida.backends.djsite.utils import get_automatic_user
    from aiida.backends.djsite.cmdline import (
        get_group_list, get_workflow_list, get_log_messages
    )
