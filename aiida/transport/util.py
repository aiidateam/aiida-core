# -*- coding: utf-8 -*-
from aiida.common.extendeddicts import FixedFieldsAttributeDict
from aiida.plugins.factory import BaseFactory


def TransportFactory(entry_point):
    """
    Return the Transport plugin class for a given entry point

    :param entry_point: the entry point name of the Transport plugin
    """
    return BaseFactory('aiida.transports', entry_point)


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
