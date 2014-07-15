from django.contrib import admin
from aiida.djsite.db.models import *

admin.site.register(DbNode)
admin.site.register(DbLink)
admin.site.register(DbPath)
admin.site.register(DbAttribute)
admin.site.register(DbGroup)
admin.site.register(DbComputer)
admin.site.register(DbAuthInfo)
admin.site.register(DbComment)



