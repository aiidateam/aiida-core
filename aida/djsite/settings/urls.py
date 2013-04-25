from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# APIs
#from tastypie.api import Api
#from aida.djsite.main.api import (CalculationResource,
#                                  CalcAttrNumResource, 
#                                  CalcAttrNumValResource, 
#                                  StructureResource,
#                                  )

#v1_api = Api(api_name='v1')
#v1_api.register(CalculationResource())
#v1_api.register(CalcAttrNumResource())
#v1_api.register(CalcAttrNumValResource())
#v1_api.register(StructureResource())

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'aida1.views.home', name='home'),
    # url(r'^aida1/', include('aida1.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
#    url(r'^api/', include(v1_api.urls)),
)
