from django.conf.urls import patterns, url

from awi import views

urlpatterns = patterns('',
	url(r'^$', views.index, name='home'), # home page
	url(r'^login', views.login_view, name='login'), #login page
	url(r'^logout', views.logout_view, name='logout'), #logout page
	url(r'^filters/get/(?P<module>[a-z0-9\-_]+)', views.filters_get, name='filters_get'), #get the filters markup for a given module
	url(r'^filters/set/(?P<module>[a-z0-9\-_]+)/(?P<field>[a-z0-9\-_]+)', views.filters_set, name='filters_set'), #get the filters markup for a given module
	url(r'^filters/remove/(?P<module>[a-z0-9\-_]+)/(?P<field>[a-z0-9\-_]+)', views.filters_remove, name='filters_remove'), #remove a filter for a given module
	url(r'^filters/create/(?P<module>[a-z0-9\-_]+)/(?P<field>[a-z0-9\-_]+)', views.filters_create, name='filters_create'), # update a filter (ajax)
	url(r'^filters/value/(?P<module>[a-z0-9\-_]+)/(?P<field>[a-z0-9\-_]+)', views.filters_value, name='filters_value'), # update a filter (ajax)
	url(r'^filters/querystring/(?P<module>[a-z0-9\-_]+)', views.filters_querystring, name='filters_querystring'), # get the querystring for filtering
	url(r'^computers/rename/(?P<computer_id>\d+)', views.computers_rename, name='computers_rename'), # rename a computer (ajax)
	url(r'^computers/detail/(?P<computer_id>\d+)', views.computers_detail, name='computers_detail'), # details for a computer called in ajax
	url(r'^computers/list/(?P<ordering>[a-z0-9\-_]+)', views.computers_list), # listing of computers
	url(r'^computers/list', views.computers_list, name='computers_list'), # listing of computers
	url(r'^computers', views.computers, name='computers'), # computers module
	url(r'^calculations/detail/(?P<calculation_id>\d+)', views.calculations_detail, name='calculations_detail'), # details for a calculation called in ajax
	url(r'^calculations/list/(?P<ordering>[a-z0-9\-_]+)', views.calculations_list), # listing of calculations
	url(r'^calculations/list', views.calculations_list, name='calculations_list'), # listing of calculations
	url(r'^calculations', views.calculations, name='calculations'), # calculations module
	url(r'^codes', views.codes, name='codes'), # page for management of codes
)