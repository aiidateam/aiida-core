from aiida.common.extendeddicts import FixedFieldsAttributeDict
from aiida.transport.transport import Transport


def TransportFactory(module):
    """
    Used to return a suitable Transport subclass.

    :param str module: name of the module containing the Transport subclass
    :return: the transport subclass located in module 'module'
    """
    from aiida.common.pluginloader import BaseFactory

    return BaseFactory(module, Transport, "aiida.transport.plugins")


class FileAttribute(FixedFieldsAttributeDict):
    """
    A class, resembling a dictionary, to describe the attributes of a file,
    that is returned by get_attribute().
    Possible keys: st_size, st_uid, st_gid, st_mode, st_atime, st_mtime
    """
    _valid_fields = (
        'st_size',
        'st_uid',
        'st_gid',
        'st_mode',
        'st_atime',
        'st_mtime',
    )