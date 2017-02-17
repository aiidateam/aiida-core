from abc import abstractproperty, ABCMeta


class Backend(object):
    """
    The public interface that defines a backend factory that creates backend
    specific concrete objects.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def log(self):
        """
        Get an object that implements the logging utilities interface.

        :return: An concrete log utils object
        :rtype: :class:`aiida.orm.log.Log`
        """
        pass


def get_backend(backend_type=None):
    """
    Create a concrete factory based on the backend or use the global backend
    if not specified.

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
            from aiida.orm.implementation.django.backend import DjangoBackend
            _DJANGO_BACKEND = DjangoBackend()
        return _DJANGO_BACKEND
    elif backend_type == 'sqlalchemy':
        global _SQLA_BACKEND
        if _SQLA_BACKEND is None:
            from aiida.orm.implementation.sqlalchemy.backend import SqlaBackend
            _SQLA_BACKEND = SqlaBackend()
        return _SQLA_BACKEND
    else:
        raise ValueError("Unknown backend, pal")


_DJANGO_BACKEND = None
_SQLA_BACKEND = None
