# -*- coding: utf-8 -*-

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