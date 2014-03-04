from django.contrib import admin
from aiida.djsite.db.models import *

admin.site.register(DbNode)
admin.site.register(DbLink)
admin.site.register(DbPath)
admin.site.register(Attribute)
admin.site.register(Group)
admin.site.register(DbComputer)
admin.site.register(AuthInfo)
admin.site.register(Comment)



