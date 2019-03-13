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
Base class for AiiDA tests
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testimplbase import AiidaTestImplementation
from aiida.orm.implementation.django.backend import DjangoBackend

# Add a new entry here if you add a file with tests under aiida.backends.djsite.db.subtests
# The key is the name to use in the 'verdi test' command (e.g., a key 'generic'
# can be run using 'verdi test db.generic')
# The value must be the module name containing the subclasses of unittest.TestCase


# This contains the codebase for the setUpClass and tearDown methods used internally by the AiidaTestCase
# This inherits only from 'object' to avoid that it is picked up by the automatic discovery of tests
# (It shouldn't, as it risks to destroy the DB if there are not the checks in place, and these are
# implemented in the AiidaTestCase
class DjangoTests(AiidaTestImplementation):
    """
    Automatically takes care of the setUpClass and TearDownClass, when needed.
    """

    # pylint: disable=attribute-defined-outside-init

    # Note this is has to be a normal method, not a class method
    def setUpClass_method(self):
        self.clean_db()
        self.backend = DjangoBackend()

    def clean_db(self):
        from aiida.backends.djsite.db import models

        # I first need to delete the links, because in principle I could not delete input nodes, only outputs.
        # For simplicity, since I am deleting everything, I delete the links first
        models.DbLink.objects.all().delete()

        # Then I delete the nodes, otherwise I cannot delete computers and users
        models.DbLog.objects.all().delete()
        models.DbNode.objects.all().delete()  # pylint: disable=no-member
        models.DbWorkflow.objects.all().delete()  # pylint: disable=no-member
        models.DbUser.objects.all().delete()  # pylint: disable=no-member
        models.DbComputer.objects.all().delete()
        models.DbGroup.objects.all().delete()

    def tearDownClass_method(self):
        """
        Backend-specific tasks for tearing down the test environment.
        """
