# -*- coding: utf-8 -*-

from __future__ import absolute_import
from aiida import settings

STORAGE_BACKEND = getattr(settings, "STORAGE_BACKEND", "django")

if STORAGE_BACKEND == "sqlalchemy":
    raise NotImplementedError
elif STORAGE_BACKEND == "django":
    from aiida.backends.djsite.utils import get_automatic_user
    from aiida.backends.djsite.cmdline import (
        get_group_list, get_workflow_list, get_log_messages
    )
