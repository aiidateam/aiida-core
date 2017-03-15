# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Plugin for PBSPro.
This has been tested on PBSPro v. 12.
"""
from __future__ import division
import aiida.scheduler
from .pbsbaseclasses import PbsBaseClass

# This maps PbsPro status letters to our own status list

## List of states from the man page of qstat
#B  Array job has at least one subjob running.
#E  Job is exiting after having run.
#F  Job is finished.
#H  Job is held.
#M  Job was moved to another server.
#Q  Job is queued.
#R  Job is running.
#S  Job is suspended.
#T  Job is being moved to new location.
#U  Cycle-harvesting job is suspended due to  keyboard  activity.
#W  Job is waiting for its submitter-assigned start time to be reached.
#X  Subjob has completed execution or has been deleted.



class PbsproScheduler(PbsBaseClass):
    """
    Subclass to support the PBSPro scheduler
    (http://www.pbsworks.com/).

    I redefine only what needs to change from the base class
    """
    _logger = aiida.scheduler.Scheduler._logger.getChild('pbspro')

    ## I don't need to change this from the base class
    #_job_resource_class = PbsJobResource

    ## For the time being I use a common dictionary, should be sufficient
    ## for the time being, but I can redefine it if needed.
    #_map_status = _map_status_pbs_common

    def _get_resource_lines(self, num_machines, num_mpiprocs_per_machine,
                            num_cores_per_machine, max_memory_kb, max_wallclock_seconds):
        """
        Return the lines for machines, memory and wallclock relative
        to pbspro.
        """
        # Note: num_cores_per_machine is not used here but is provided by
        #       the parent class ('_get_submit_script_header') method

        return_lines = []

        select_string = "select={}".format(num_machines)
        if num_mpiprocs_per_machine:
            select_string += ":mpiprocs={}".format(num_mpiprocs_per_machine)
        if num_cores_per_machine:
            select_string += ":ppn={}".format(num_cores_per_machine)

        if max_wallclock_seconds is not None:
            try:
                tot_secs = int(max_wallclock_seconds)
                if tot_secs <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError(
                    "max_wallclock_seconds must be "
                    "a positive integer (in seconds)! It is instead '{}'"
                    "".format(max_wallclock_seconds))
            hours = tot_secs // 3600
            tot_minutes = tot_secs % 3600
            minutes = tot_minutes // 60
            seconds = tot_minutes % 60
            return_lines.append("#PBS -l walltime={:02d}:{:02d}:{:02d}".format(
                hours, minutes, seconds))

        if max_memory_kb:
            try:
                virtualMemoryKb = int(max_memory_kb)
                if virtualMemoryKb <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError(
                    "max_memory_kb must be "
                    "a positive integer (in kB)! It is instead '{}'"
                    "".format((max_memory_kb)))
            select_string += ":mem={}kb".format(virtualMemoryKb)

        return_lines.append("#PBS -l {}".format(select_string))
        return return_lines
