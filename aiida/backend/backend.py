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