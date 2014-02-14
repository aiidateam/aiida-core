from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# API-related classes
from tastypie.api import Api
from aiida.djsite.db.api import (
    MetadataResource,
    AuthInfoResource,
    DbAttributeResource,
    AttributeResource,
    DbComputerResource,
    DbNodeResource,
    UserResource,
    )

# We register the API v.1
v1_api = Api(api_name='v1')
v1_api.register(DbComputerResource())
v1_api.register(UserResource())
v1_api.register(AuthInfoResource())
v1_api.register(DbNodeResource())
v1_api.register(DbAttributeResource())
v1_api.register(AttributeResource())
v1_api.register(MetadataResource())

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'aiida1.views.home', name='home'),
    # url(r'^aiida1/', include('aiida1.foo.urls')),
    ## Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include(v1_api.urls)),
)
