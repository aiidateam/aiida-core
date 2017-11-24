# -*- coding: utf-8 -*-
from abc import abstractproperty, ABCMeta
from aiida.backends import settings
from aiida.repository.implementation.filesystem.repository import FileSystemRepository

_FILESYSTEM_BACKEND = None

def construct_backend(backend_type=None, backend_config=None):
    """
    Construct a concrete repository backend instance based on the backend_type
    or use the global repository backend value if not specified.

    :param backend_type: get a repository backend instance based on the specified type (or default)
    :param backend_config: a dictionary with the parameters required to construct and configure the backend
    :return: :class:`Repository`
    """
    if backend_type is None:
        backend_type = settings.REPOSITORY_BACKEND
        backend_config = settings.REPOSITORY_CONFIG

    if backend_config is None:
        raise ValueError("no backend configuration dictionary specified")

    if backend_type == 'filesystem':
        global _FILESYSTEM_BACKEND
        if _FILESYSTEM_BACKEND is None:
            _FILESYSTEM_BACKEND = FileSystemRepository(backend_config)
        return _FILESYSTEM_BACKEND
    else:
        raise ValueError("The specified repository backend '{}' is currently not supported".format(backend_type))