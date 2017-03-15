# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.scheduler.plugins.direct import DirectScheduler
from aiida.scheduler.datastructures import job_states
from aiida.scheduler import SchedulerError

import unittest
# import logging
#import uuid

#This was executed with ps -o pid,stat,user,time | tail -n +2
mac_ps_output_str="""21259 S+   broeder   0:00.04
87619 S+   broeder   0:00.44
87634 S+   broeder   0:00.01
87649 S+   broeder   0:00.02
87664 S+   broeder   0:00.01
87679 S+   broeder   0:00.01
87694 S+   broeder   0:00.01
87711 S+   broeder   0:00.01
87726 S+   broeder   0:00.02
87741 S+   broeder   0:00.01
87756 S+   broeder   0:00.01
87771 S+   broeder   0:00.01
87787 S+   broeder   0:00.02
87803 S+   broeder   0:00.01
87818 S+   broeder   0:00.02
87834 S+   broeder   0:00.02
87849 S+   broeder   0:00.11
87865 S+   broeder   0:00.02
87880 S+   broeder   0:00.02
15967 S+   broeder   0:00.05
87910 S+   broeder   0:00.02
87925 S+   broeder   0:00.02
16814 S    broeder   0:00.02
24516 S+   broeder   0:00.06
"""
linux_ps_output_str="""11354 Ss   aiida    00:00:00
11383 R+   aiida    00:00:00
11384 S+   aiida    00:00:00
"""

wrong_output="""aaa"""


class TestParserGetJobList(unittest.TestCase):
    """
    Tests to verify if teh function _parse_joblist_output behave correctly
    The tests is done parsing a string defined above, to be used offline
    """

    def test_parse_mac_wrong(self):
        """
        Test whether _parse_joblist can parse the qstat -f output
        """
        s = DirectScheduler()

        with self.assertRaises(SchedulerError):
            result = s._parse_joblist_output(
                retval=0, stdout=wrong_output, stderr="")

    def test_parse_mac_joblist_output(self):
        """
        Test whether _parse_joblist can parse the qstat -f output
        """
        s = DirectScheduler()

        result = s._parse_joblist_output(
            retval=0, stdout=mac_ps_output_str, stderr="")
        self.assertEqual(len(result), 24)

        job_ids = [job.job_id for job in result]
        self.assertIn("87849", job_ids)


    def test_parse_linux_joblist_output(self):
        """
        Test whether _parse_joblist can parse the qstat -f output
        """
        s = DirectScheduler()

        result = s._parse_joblist_output(
            retval=0, stdout=linux_ps_output_str, stderr="")
        self.assertEqual(len(result), 3)

        job_ids = [job.job_id for job in result]
        self.assertIn("11383", job_ids)


if __name__ == '__main__':        
    unittest.main()
