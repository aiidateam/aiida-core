from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotAllowed
import json

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
	# to have something to show for testing purposes, manually store a session data for 2 filters
	if 'filters' not in request.session:
		request.session['filters'] = {}
	if module not in request.session['filters']:
		request.session['filters'][module] = {}
	
	if 'description' not in request.session['filters'][module]:
		request.session['filters'][module]['description'] = {
			'type': 'text', # possible values : boolean, numeric, text, list, date
			'display_name': 'Description',
			'operator': 'icontains',
				#for boolean : exact
				#for numeric : gt, gte, lt, lte, iexact, range
				#for text : iexact, icontains, istartswith, iendswith, isnull
				#for list : not used, but should be 'exact'. The possible values are taken from the API schema
				#for date : range, year, month, day, week_day
			'value': 'epfl',
		}
	if 'scheduler_type' not in request.session['filters'][module]:
		request.session['filters'][module]['scheduler_type'] = {
			'type': 'list',
			'display_name': 'Scheduler',
			'operator': 'exact',
			'value': 'pbspro',
		}
	#return HttpResponse(json.dumps(request.session['filters']))
	request.session.modified = True #this needs to go away once the testing code above is deleted
	return render(request, 'awi/filters_markup.html', {'module': module, 'filters': request.session['filters'][module]})

@login_required(login_url='awi:login')
def filters_set(request, module, field):
	"""
	Set one filter for a given module or update said filter
	"""
	if request.method == 'POST':
		# we might get : type, display_name, operator, value
		# check if we have already a filter for this module and this field
		# if yes, then we need to update the data (can only update operator and value)
		# if not, we create the filter but we need to get the schema in the API to know the type and display_name
		
		# get the type from the API to allow proper validation
		
		operator = request.POST.get('operator', None)
		value = request.POST.get('value', None)
		if 'type' in request.session['filters'][module][field]: # the filter exists, we need to update
			if operator is not None:
				request.session['filters'][module][field]['operator'] = operator
			if value is not None:
				#validation
				value = value.strip()
				if not value:
					return HttpResponse("The operator value cannot be empty", status=400)
				else:
					request.session['filters'][module][field]['value'] = value
			request.session.modified = True
			return HttpResponse(json.dumps(request.session['filters'][module][field]))
		else:
			if operator is not None and value is not None:
				# here we lookup the schema via the API to know the type and display_name
				return HttpResponse("created filter")
			else:
				response = HttpResponse("You need to provide operator and value to create a filter", status=400)
				return response
	else:
		# if we didn't receive POST data, return a 405 error (method not allowed)
		return HttpResponseNotAllowed(['POST'])

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
	return render(request, 'awi/filters_create.html', {'module': module, 'field': field})

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
