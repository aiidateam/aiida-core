# -*- coding: utf-8 -*-

import plum.persistence.process_record
from abc import ABCMeta, abstractproperty


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


class ProcessRecord(plum.persistence.process_record.ProcessRecord):
    __metaclass__ = ABCMeta

    def __init__(self):
        super(ProcessRecord, self).__init__()

    @abstractproperty
    def user(self):
        pass

    @abstractproperty
    def calculation_node(self):
        pass
