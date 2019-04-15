# -*- coding: utf-8 -*-

from aiida.backends.settings import BACKEND
from aiida.common.exceptions import ConfigurationError
from aiida.orm.implementation.general.group import get_group_type_mapping
from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"

if BACKEND == BACKEND_SQLA:
    from aiida.orm.implementation.sqlalchemy.node import Node
    from aiida.orm.implementation.sqlalchemy.computer import Computer
    from aiida.orm.implementation.sqlalchemy.group import Group
    from aiida.orm.implementation.sqlalchemy.lock import Lock, LockManager
    # from aiida.orm.implementation.sqlalchemy.querytool import QueryTool
    from aiida.orm.implementation.sqlalchemy.workflow import Workflow, kill_all, get_workflow_info, get_all_running_steps
    from aiida.orm.implementation.sqlalchemy.code import Code, delete_code
    from aiida.orm.implementation.sqlalchemy.comment import Comment
    from aiida.orm.implementation.sqlalchemy.user import User
    from aiida.orm.implementation.sqlalchemy.utils import delete_computer
    from aiida.backends.querybuild.querybuilder_sa import QueryBuilder
    from aiida.backends.sqlalchemy import models
elif BACKEND == BACKEND_DJANGO:
    from aiida.orm.implementation.django.node import Node
    from aiida.orm.implementation.django.computer import Computer
    from aiida.orm.implementation.django.group import Group
    from aiida.orm.implementation.django.lock import Lock, LockManager
    from aiida.orm.implementation.django.querytool import QueryTool
    from aiida.orm.implementation.django.workflow import Workflow, kill_all, get_workflow_info, get_all_running_steps
    from aiida.orm.implementation.django.code import Code, delete_code
    from aiida.orm.implementation.django.comment import Comment
    from aiida.orm.implementation.django.user import User
    from aiida.orm.implementation.django.utils import delete_computer
    from aiida.backends.querybuild.querybuilder_django import QueryBuilder
    from aiida.backends.djsite.db import models
elif BACKEND is None:
    raise ConfigurationError("settings.BACKEND has not been set.\n"
                             "Hint: Have you called aiida.load_dbenv?")
else:
    raise ConfigurationError("Unknown settings.BACKEND: {}".format(
        BACKEND))
