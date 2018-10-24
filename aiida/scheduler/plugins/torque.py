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
Plugin for PBS/Torque.
This has been tested on Torque v.2.4.16 (from Ubuntu).
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
import logging

from .pbsbaseclasses import PbsBaseClass

_LOGGER = logging.getLogger(__name__)

## These are instead the states from PBS/Torque v.2.4.16 (from Ubuntu)
# C -  Job is completed after having run [different from above, but not clashing]
# E -  Job is exiting after having run. [same as above]
# H -  Job is held. [same as above]
# Q -  job is queued, eligible to run or routed. [same as above]
# R -  job is running. [same as above]
# T -  job is being moved to new location. [same as above]
# W -  job is waiting for its execution time
#     (-a option) to be reached. [similar to above]
# S -  (Unicos only) job is suspend. [as above]


class TorqueScheduler(PbsBaseClass):
    """
    Subclass to support the Torque scheduler..

    I redefine only what needs to change from the base class
    """

    ## I don't need to change this from the base class
    # _job_resource_class = PbsJobResource

    ## For the time being I use a common dictionary, should be sufficient
    ## for the time being, but I can redefine it if needed.
    # _map_status = _map_status_pbs_common

    def _get_resource_lines(self, num_machines, num_mpiprocs_per_machine, num_cores_per_machine, max_memory_kb,
                            max_wallclock_seconds):
        """
        Return the lines for machines, memory and wallclock relative
        to pbspro.
        """
        return_lines = []

        select_string = "nodes={}".format(num_machines)
        if num_cores_per_machine:
            select_string += ":ppn={}".format(num_cores_per_machine)
        elif num_mpiprocs_per_machine:
            # if num_cores_per_machine is not defined then use
            # num_mpiprocs_per_machine
            select_string += ":ppn={}".format(num_mpiprocs_per_machine)

        if max_wallclock_seconds is not None:
            try:
                tot_secs = int(max_wallclock_seconds)
                if tot_secs <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError("max_wallclock_seconds must be "
                                 "a positive integer (in seconds)! It is instead '{}'"
                                 "".format(max_wallclock_seconds))
            hours = tot_secs // 3600
            tot_minutes = tot_secs % 3600
            minutes = tot_minutes // 60
            seconds = tot_minutes % 60
            # There is always something before, at least the total #
            # of nodes
            select_string += (",walltime={:02d}:{:02d}:{:02d}".format(hours, minutes, seconds))

        if max_memory_kb:
            try:
                virtual_memory_kb = int(max_memory_kb)
                if virtual_memory_kb <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError("max_memory_kb must be "
                                 "a positive integer (in kB)! It is instead '{}'"
                                 "".format((max_memory_kb)))
            # There is always something before, at least the total #
            # of nodes
            select_string += ",mem={}kb".format(virtual_memory_kb)

        return_lines.append("#PBS -l {}".format(select_string))
        return return_lines
