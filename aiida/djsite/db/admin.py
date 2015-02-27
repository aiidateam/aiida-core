# -*- coding: utf-8 -*-
from django.contrib import admin
from aiida.djsite.db.models import *

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.0"

admin.site.register(DbNode)
admin.site.register(DbLink)
admin.site.register(DbPath)
admin.site.register(DbAttribute)
admin.site.register(DbGroup)
admin.site.register(DbComputer)
admin.site.register(DbAuthInfo)
admin.site.register(DbComment)



