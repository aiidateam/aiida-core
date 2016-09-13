

import plum.class_loader
import plum.util
from aiida.common.lang import override


class ClassLoader(plum.class_loader.ClassLoader):
    @staticmethod
    def is_wrapped_job_calculation(name):
        from aiida.workflows2.legacy.job_process import JobProcess

        return name.find(JobProcess.__name__) != -1

    @override
    def find_class(self, name):
        from aiida.workflows2.legacy.job_process import JobProcess

        if self.is_wrapped_job_calculation(name):
            idx = name.find(JobProcess.__name__)
            wrapped_class = name[idx + len(JobProcess.__name__) + 1:]
            # Recreate the class
            return JobProcess.build(plum.util.load_class(wrapped_class))
