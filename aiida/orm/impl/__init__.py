from __future__ import absolute_import
from aiida import settings

STORAGE_BACKEND = getattr(settings, "STORAGE_BACKEND", "django")

if STORAGE_BACKEND == "sqlalchemy":
    raise NotImplemented
elif STORAGE_BACKEND == "django":
    from aiida.orm.impl.django.node import Node
    from aiida.orm.impl.django.computer import Computer
    from aiida.orm.impl.django.group import Group
    from aiida.orm.impl.django.lock import Lock
    from aiida.orm.impl.django.querytool import QueryTool
    from aiida.orm.impl.django.workflow import Workflow
    from aiida.orm.impl.django.code import Code
    from aiida.orm.impl.django.utils import delete_computer

    from django.core.exceptions import ObjectDoesNotExist
