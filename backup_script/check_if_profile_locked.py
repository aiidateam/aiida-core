# -*- coding: utf-8 -*-
"""
Simple script to check if an AiiDA profile is locked
(e.g. when doing `verdi storage maintain --full`)
"""
from aiida.common.exceptions import LockedProfileError
from aiida.manage import get_manager
from aiida.manage.profile_access import ProfileAccessManager

try:
    ProfileAccessManager(get_manager().get_config().get_profile('mc3d')).request_access()
    print(0)
except LockedProfileError:
    print(1)
