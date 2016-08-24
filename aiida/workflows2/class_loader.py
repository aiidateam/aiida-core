

import plum.class_loader
import plum.util
from aiida.common.lang import override


class ClassLoader(plum.class_loader.ClassLoader):
    @override
    def find_class(self, name):
        from aiida.workflows2.legacy.job_process import JobProcess

        idx = name.find(JobProcess.__name__)
        if idx != -1:
            wrapped_class = name[idx + len(JobProcess.__name__) + 1:]
            # Recreate the class
            return JobProcess.build(plum.util.load_class(wrapped_class))

