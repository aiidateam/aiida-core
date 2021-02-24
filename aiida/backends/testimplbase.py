# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Implementation-dependednt base tests"""
from abc import ABC, abstractmethod


class AiidaTestImplementation(ABC):
    """Backend-specific test implementations."""
    _backend = None

    @property
    def backend(self):
        """Get the backend."""
        if self._backend is None:
            from aiida.manage.manager import get_manager
            self._backend = get_manager().get_backend()

        return self._backend

    @abstractmethod
    def clean_db(self):
        """This method fully cleans the DB."""
