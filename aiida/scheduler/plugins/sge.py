"""
Plugin for SGE.
This has been tested on XXX.
"""
from __future__ import division
import aiida.scheduler
from aiida.common.utils import escape_for_bash
from aiida.scheduler import SchedulerError, SchedulerParsingError
from aiida.scheduler.datastructures import (
    JobInfo, job_states, MachineInfo)

# You may want to follow the way PBSPro and SLURM plugins are done.

# At the end (or, rather, maybe even at the beginning, before writing the code)
# you should write test cases in a file called test_sge.py (follow what is
# done for the other test_*.py files, and improve if you want!) to test if
# the plugin is working as expected.
# The best is to take an actual output from you cluster, anonymize it removing
# real usernames, and reducing the actual output to a small enough number of
# jobs, that are however still representative (e.g. one running, one queued, 
# one held, ...)

# Moreover: while writing the plugin, try to make full use of the manual pages
# and manuals of the scheduler. If there is something that is not documented,
# mark it in the code with a # TODO: xxx explanation xxx
# inside the code, for later improvement.

# As far as I understand, sge has a -xml option; I think that this is
# the best way to get the output to be then parsed.
# To parse XML, use
#    import xml.dom.minidom
# and the parsing function
#    dom = xml.dom.minidom.parse(f)
# (this is for file-like objects f, I think there is also a function for 
# strings, otherwise you can convert a string to a file-like using StringIO)
# Then you can get tags and their content using things like:
#   var = dom.getElementsByTagName('var')
#   var.getAttribute('name').lower()
# etc. Refer to the xml.dom.minidom documentation for more details. 

# Note that there are the following functions defined in the slurm and pbspro
# schedulers: you may want to copy them here and adapt them for the sge
# scheduler.
#slurm.py:    def _convert_time(self,string):
#slurm.py:    def _parse_time_string(self,string,fmt='%Y-%m-%dT%H:%M:%S'):
#pbspro.py:    def _convert_time(self,string):
#pbspro.py:    def _parse_time_string(self,string,fmt='%a %b %d %H:%M:%S %Y'):

class SgeScheduler(aiida.scheduler.Scheduler):
    """
    SGE implementation of the scheduler functions.
    """
    _logger = aiida.scheduler.Scheduler._logger.getChild('sge')

    def _get_joblist_command(self,jobs=None): 
        raise NotImplementedError

    def _get_detailed_jobinfo_command(self,jobid):
        raise NotImplementedError

    def _get_submit_script_header(self, job_tmpl):
        raise NotImplementedError

    def _get_submit_command(self, submit_script):
        raise NotImplementedError

    def _parse_joblist_output(self, retval, stdout, stderr):
        raise NotImplementedError

    def _parse_submit_output(self, retval, stdout, stderr):
        raise NotImplementedError


