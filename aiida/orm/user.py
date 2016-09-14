# -*- coding: utf-8 -*-

from aiida.orm.implementation import User
import aiida.orm.utils as utils

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"


class Util(utils.BackendDelegateWithDefault):
    @classmethod
    def create_default(cls):
        # Fall back to Django
        from aiida.orm.implementation.django.user import Util as UserUtil
        return Util(UserUtil())

    def delete_user(self, pk):
        return self._backend.delete_user(pk)