# -*- coding: utf-8 -*-
from enum import Enum



class LinkType(Enum):
    """
    A simple enum of allowed link types.
    """
    UNSPECIFIED = 'unspecified'
    CREATE = 'createlink'
    RETURN = 'returnlink'
    INPUT = 'inputlink'
    CALL = 'calllink'
