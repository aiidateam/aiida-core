# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################


import plum.class_loader
import plum.util
from aiida.common.lang import override


class ClassLoader(plum.class_loader.ClassLoader):
    @staticmethod
    def is_wrapped_job_calculation(name):
        from aiida.work.legacy.job_process import JobProcess

        return name.find(JobProcess.__name__) != -1

    @override
    def find_class(self, name):
        from aiida.work.legacy.job_process import JobProcess

        if self.is_wrapped_job_calculation(name):
            idx = name.find(JobProcess.__name__)
            wrapped_class = name[idx + len(JobProcess.__name__) + 1:]
            # Recreate the class
            return JobProcess.build(plum.util.load_class(wrapped_class))


# The default class loader instance
_CLASS_LOADER = plum.class_loader.ClassLoader(ClassLoader())

def get_default():
    pass