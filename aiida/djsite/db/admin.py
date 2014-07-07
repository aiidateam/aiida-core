# -*- coding: utf-8 -*-
from django.contrib import admin
from aiida.djsite.db.models import *

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = "Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

admin.site.register(DbNode)
admin.site.register(DbLink)
admin.site.register(DbPath)
admin.site.register(DbAttribute)
admin.site.register(DbGroup)
admin.site.register(DbComputer)
admin.site.register(DbAuthInfo)
admin.site.register(DbComment)



