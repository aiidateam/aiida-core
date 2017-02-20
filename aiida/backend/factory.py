from abc import abstractproperty, ABCMeta

_DJANGO_BACKEND = None
_SQLA_BACKEND   = None

class BackendFactory(object):
    """
    Factory class that can instantiate the correct subclass of Backend
    depending on the backend type specified or defined in the settings
    """

    def construct(self, backend_type=None):
        """
        Construct a concrete backend instance based on the backend_type
        or use the global backend value if not specified.

        :param backend_type: Get a backend instance based on the specified
            type (or default)
        :return: :class:`Backend`
        """
        if backend_type is None:
            from aiida.backends import settings
            backend_type = settings.BACKEND

        if backend_type == 'django':
            global _DJANGO_BACKEND
            if _DJANGO_BACKEND is None:
                from aiida.backend.django.backend import DjangoBackend
                _DJANGO_BACKEND = DjangoBackend()
            return _DJANGO_BACKEND
        elif backend_type == 'sqlalchemy':
            global _SQLA_BACKEND
            if _SQLA_BACKEND is None:
                from aiida.backend.sqlalchemy.backend import SqlaBackend
                _SQLA_BACKEND = SqlaBackend()
            return _SQLA_BACKEND
        else:
            raise ValueError("The specified backend {} is currently not implemented".format(backend_type))