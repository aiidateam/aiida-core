# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.backends.settings import BACKEND
from aiida.common.exceptions import ConfigurationError
from aiida.orm.implementation.general.group import get_group_type_mapping
from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA


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
    from aiida.backends.djsite.db import models
elif BACKEND is None:
    raise ConfigurationError("settings.BACKEND has not been set.\n"
                             "Hint: Have you called aiida.load_dbenv?")
else:
    raise ConfigurationError("Unknown settings.BACKEND: {}".format(
        BACKEND))

from aiida.orm.computer import delete_computer
