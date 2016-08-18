

import plum.class_loader
import plum.util
from aiida.workflows2.legacy.job_process import JobProcess


class ClassLoader(plum.class_loader.ClassLoader):
    def find_class(self, name):
        if name.startswith(JobProcess.__name__):
            wrapped_class = name[len(JobProcess.__name__) + 1:]
            # Recreate the class
            return JobProcess.build(plum.util.load_class(wrapped_class))

# The default class loader for AiiDA workflows
LOADER = plum.class_loader.ClassLoader(ClassLoader)