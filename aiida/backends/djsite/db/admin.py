# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from django.contrib import admin

from .models import DbNode, DbLink, DbPath, DbAttribute, DbGroup, DbComputer, DbAuthInfo, DbComment


admin.site.register(DbNode)
admin.site.register(DbLink)
admin.site.register(DbPath)
admin.site.register(DbAttribute)
admin.site.register(DbGroup)
admin.site.register(DbComputer)
admin.site.register(DbAuthInfo)
admin.site.register(DbComment)
