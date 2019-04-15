# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import DbNode, DbLink, DbPath, DbAttribute, DbGroup, DbComputer, DbAuthInfo, DbComment

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0.1"
__authors__ = "The AiiDA team."

admin.site.register(DbNode)
admin.site.register(DbLink)
admin.site.register(DbPath)
admin.site.register(DbAttribute)
admin.site.register(DbGroup)
admin.site.register(DbComputer)
admin.site.register(DbAuthInfo)
admin.site.register(DbComment)
