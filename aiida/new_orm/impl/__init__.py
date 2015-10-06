from aiida import settings

if not hasattr(settings, "STORAGE_BACKEND"):
    STORAGE_BACKEND = "django"

if STORAGE_BACKEND == "sqlalchemy":
    raise NotImplemented
elif STORAGE_BACKEND == "django":
    from aiida.new_orm.impl.django.node import Node
    from aiida.new_orm.impl.django.computer import Computer
    from aiida.new_orm.impl.django.group import Group
    from aiida.new_orm.impl.django.lock import Lock
    from aiida.new_orm.impl.django.querytool import QueryTool
    from aiida.new_orm.impl.django.workflow import Workflow
