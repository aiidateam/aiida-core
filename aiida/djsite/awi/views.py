from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotAllowed
from aiida.djsite.db.api import (
	AttributeResource,
	DbAttributeResource,
	DbAuthInfoResource,
	DbComputerResource,
	DbGroupResource,
	DbNodeResource,
	MetadataResource,
	UserResource,
	)
import json
import datetime, dateutil.parser

def index(request):
	"""
	Home page view
	"""
	return render(request, 'awi/base_home.html')

def login_view(request):
	"""
	Login view
	"""
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		next = request.POST['next']
		user = authenticate(username=username, password=password)
		if user is not None:
			if user.is_active:
				if not request.POST.get('remember', None):
					request.session.set_expiry(0)
				login(request, user)
				if next:
					return redirect(next)
				else:
					return redirect('awi:home')
			else:
				return render(request, 'awi/login_form.html', {'base_template': 'awi/base_login.html', 'error_message': 'Account disabled'})
		else:
			return render(request, 'awi/login_form.html', {'base_template': 'awi/base_login.html', 'error_message': 'Wrong username or password'})
	else:
		try:
			next = request.GET['next']
		except:
			next = 'awi:home'
		
		return render(request, 'awi/login_form.html', {'base_template': 'awi/base_login.html', 'next': next})

def logout_view(request):
	"""
	Logout view
	"""
	logout(request)
	return redirect('awi:home') #redirect

#Filters views
@login_required(login_url='awi:login')
def filters_get(request, module):
	"""
	Get the html markup for filters of a given module
	"""
	# create the filters session data if not already created
	if 'filters' not in request.session:
		request.session['filters'] = {}
	if module not in request.session['filters']:
		request.session['filters'][module] = {}
	
	request.session.modified = True
	return render(request, 'awi/filters_markup.html', {'module': module, 'filters': request.session['filters'][module]})

@login_required(login_url='awi:login')
def filters_set(request, module, field):
	"""
	Set one filter for a given module or update said filter
	"""
	# create the filters session data if not already created
	if 'filters' not in request.session:
		request.session['filters'] = {}
	if module not in request.session['filters']:
		request.session['filters'][module] = {}
	if field not in request.session['filters'][module]:
		request.session['filters'][module][field] = {}
	
	if request.method == 'POST':
		# we might get : operator, value
		# check if we have already a filter for this module and this field
		# if yes, then we need to update the data
		# if not, we create the filter but we need to get the schema in the API to know the type and display_name
		
		#this needs to be hardcoded for now, unfortunately
		if module == 'computers':
			res = DbComputerResource()
		
		schema = res.build_schema()
		field_type = schema['fields'][field]['filtering']['type']
		display_name = schema['fields'][field]['display_name']
		# get the type from the API to allow proper validation
		
		operator = request.POST.get('operator', None)
		value = request.POST.get('value', None)
		if 'type' in request.session['filters'][module][field]: # the filter exists, we need to update
			if operator is not None:
				request.session['filters'][module][field]['operator'] = operator
			if value is not None:
				value = value.strip()
				if not value:
					return HttpResponse("The operator value cannot be empty", status=400)
				else:
					#validation
					if field_type == 'boolean':
						if value not in ['true', 'false']:
							return HttpResponse("Value must be a boolean (true/false)", status=400)
					elif field_type == 'numeric':
						try:
							float(value)
						except ValueError:
							return HttpResponse("Value must be numeric", status=400)
					elif field_type == 'list':
						valid_choices = schema["fields"][field]["valid_choices"]
						if value not in valid_choices:
							return HttpResponse("Value is not acceptable", status=400)
					elif field_type == 'date':
						if value.find(';') != -1:
							begin_date, end_date = value.split(';')
							try:
								begin_date = dateutil.parser.parse(begin_date)
								end_date = dateutil.parser.parse(end_date)
							except:
								return HttpResponse("Datetime format parsing error", status=400)
							if begin_date > end_date:
								return HttpResponse("Begin datetime of the range is greater than the end datetime", status=400)
						else:
							try:
								date = dateutil.parser.parse(value)
							except:
								return HttpResponse("Datetime format parsing error", status=400)
					request.session['filters'][module][field]['value'] = value
			request.session.modified = True
			return HttpResponse(json.dumps(request.session['filters'][module][field]))
		else:
			if operator is not None and value is not None:
				# we create the filter
				request.session['filters'][module][field] = {
					'type': field_type,
					'display_name': display_name,
					'operator': operator,
					'value': value,
				}
				#for boolean : exact
				#for numeric : gt, gte, lt, lte, iexact, range
				#for text : iexact, icontains, istartswith, iendswith, isnull
				#for list : not used, but should be 'exact'. The possible values are taken from the API schema
				#for date : range, year, month, day, week_day
				#http://localhost:8000/api/v1/dbnode/?ctime__range=2014-03-06T00:00&ctime__range=2014-03-08T00:00
				request.session.modified = True
				return HttpResponse(json.dumps(request.session['filters'][module][field]))
			else: 
				return HttpResponse("You need to provide operator and value to create a filter", status=400)
	else:
		# if we didn't receive POST data, return a 405 error (method not allowed)
		return HttpResponseNotAllowed(['POST'])

@login_required(login_url='awi:login')
def filters_remove(request, module, field):
	"""
	Remove a filter of a given module
	"""
	# create the filters session data if not already created
	if field in request.session['filters'][module]:
		request.session['filters'][module].pop(field, None)
		request.session.modified = True
	
	return HttpResponse(json.dumps(request.session['filters'][module]))

@login_required(login_url='awi:login')
def filters_querystring(request, module):
	"""
	Return the querystring for filtering
	"""
	output = ''
	for field, f in request.session['filters'][module].items():
		output += '&'+field+'__'+f['operator']+'='+f['value']
	return HttpResponse(output)

@login_required(login_url='awi:login')
def filters_create(request, module, field):
	"""
	Form to create a new filter
	"""
	#this needs to be hardcoded for now, unfortunately
	if module == 'computers':
		res = DbComputerResource()
	schema = res.build_schema()
	field_type = schema['fields'][field]['filtering']['type']
	display_name = schema['fields'][field]['display_name']
	
	return render(request, 'awi/filters_create.html', {'module': module, 'field': field, 'display_name': display_name, 'type': field_type})

@login_required(login_url='awi:login')
def filters_value(request, module, field):
	"""
	Update value form for filters
	"""
	return render(request, 'awi/filters_value.html', {'module': module, 'field': field,
		'display_name': request.session['filters'][module][field]["display_name"],
		'operator': request.session['filters'][module][field]["operator"],
		'type': request.session['filters'][module][field]["type"]})

# Computers views
@login_required(login_url='awi:login')
def computers(request):
	"""
	Computers default view, calls list
	"""
	return computers_list(request)

@login_required(login_url='awi:login')
def computers_list(request, ordering = 'id'):
	"""
	List of computers
	"""
	return render(request, 'awi/computers_list.html', {'ordering': ordering})

@login_required(login_url='awi:login')
def computers_detail(request, computer_id):
	"""
	Details of a computer
	"""
	api_detail_url = reverse('api_dispatch_detail', kwargs={'api_name': 'v1', 'resource_name':'dbcomputer', 'pk':computer_id})
	return render(request, 'awi/computers_detail.html', {'api_detail_url': api_detail_url, 'computer_id': computer_id})

@login_required(login_url='awi:login')
def computers_rename(request, computer_id):
	"""
	Rename form for computers
	"""
	return render(request, 'awi/computers_rename.html', {'computer_id': computer_id})

def codes(request):
	"""
	Codes page view
	"""
	return render(request, 'awi/base_codes.html')
