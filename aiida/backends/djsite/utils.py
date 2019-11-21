# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions specific to the Django backend."""


def delete_nodes_and_connections_django(pks_to_delete):  # pylint: disable=invalid-name
    """Delete all nodes corresponding to pks in the input.

    :param pks_to_delete: A list, tuple or set of pks that should be deleted.
    """
    # pylint: disable=no-member,import-error,no-name-in-module
    from django.db import transaction
    from django.db.models import Q
    from aiida.backends.djsite.db import models
    with transaction.atomic():
        # This is fixed in pylint-django>=2, but this supports only py3
        # Delete all links pointing to or from a given node
        models.DbLink.objects.filter(Q(input__in=pks_to_delete) | Q(output__in=pks_to_delete)).delete()
        # now delete nodes
        models.DbNode.objects.filter(pk__in=pks_to_delete).delete()
