# -*- coding: utf-8 -*-


from aiida.backends.settings import BACKEND

if BACKEND == "sqlalchemy":
    from aiida.backends.querybuild.querybuilder_sa import QueryBuilder
elif BACKEND == "django":
    from aiida.backends.querybuild.querybuilder_django import QueryBuilder
else:
    raise ConfigurationError("Invalid settings.BACKEND: {}".format(
            BACKEND))
