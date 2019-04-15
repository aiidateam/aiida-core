# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse_lazy
from django.views.generic import RedirectView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0.1"
__authors__ = "The AiiDA team."

admin.autodiscover()

urlpatterns = patterns('',
                       # Examples:
                       # url(r'^$', 'aiida1.views.home', name='home'),
                       # url(r'^aiida1/', include('aiida1.foo.urls')),
                       ## Uncomment the admin/doc line below to enable admin documentation:
                       # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       url(r'^admin/', include(admin.site.urls)),
)
