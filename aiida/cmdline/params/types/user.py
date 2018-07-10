"""
User param type for click
"""

import click

from aiida.cmdline.utils.decorators import with_dbenv


class UserParamType(click.ParamType):
    """
    The user parameter type for click.   Can get or create a user.
    """
    name = 'user'

    def __init__(self, create=False):
        """
        :param create: If the user does not exist, create a new instance (unstored).
        """
        self._create = create

    @with_dbenv()
    def convert(self, value, param, ctx):
        from aiida.orm.backend import construct_backend

        backend = construct_backend()
        results = backend.users.find(email=value)

        if not results:
            if self._create:
                return backend.users.create(email=value)
            else:
                self.fail("User '{}' not found".format(value), param, ctx)
        elif len(results) > 1:
            self.fail("Multiple users found with email '{}': {}".format(value, results))

        return results[0]
