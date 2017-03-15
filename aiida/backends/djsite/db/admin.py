# -*- coding: utf-8 -*-
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
