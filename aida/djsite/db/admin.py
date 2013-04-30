from django.contrib import admin
from aida.djsite.db.models import *

admin.site.register(Node)
admin.site.register(Link)
admin.site.register(Path)
admin.site.register(Attribute)
admin.site.register(Group)
admin.site.register(Computer)
admin.site.register(RunningJob)
admin.site.register(AuthInfo)
admin.site.register(Comment)


