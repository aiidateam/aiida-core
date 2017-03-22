# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.orm.implementation import User
import aiida.orm.utils as utils



class Util(utils.BackendDelegateWithDefault):
    @classmethod
    def create_default(cls):
        # Fall back to Django
        from aiida.orm.implementation.django.user import Util as UserUtil
        return Util(UserUtil())

    def delete_user(self, pk):
        return self._backend.delete_user(pk)