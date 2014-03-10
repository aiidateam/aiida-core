from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login

def index(request):
	"""
	Home page view
	"""
	return render(request, 'awi/base_home.html')

def login(request):
	"""
	Login view
	"""
	if request.POST:
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(username=username, password=password)
		if user is not None:
			if user.is_active:
				login(request, user)
				return index(request) #success
			else:
				return render(request, 'awi/base_login.html', {'error_message': 'Account disabled'})
		else:
			return render(request, 'awi/base_login.html', {'error_message': 'Wrong username or password'})
	else:
		return render(request, 'awi/base_login.html')

# Computers page view
def computers(request):
	"""
	Computers default view, calls list
	"""
	return computers_list(request)

def computers_list(request, ordering = 'id'):
	"""
	List of computers
	"""
	return render(request, 'awi/computers_list.html', {'ordering': ordering})

def computers_detail(request, computer_id, ajax = ''):
	"""
	Details of a computer
	"""
	if ajax == 'ajax':
		base_template = 'awi/base_ajax.html'
		ajax = True
	else:
		base_template = 'awi/computers_detail.html'
		ajax = False
	api_detail_url = reverse('api_dispatch_detail', kwargs={'api_name': 'v1', 'resource_name':'dbcomputer', 'pk':computer_id})
	return render(request, 'awi/computers_detail_content.html', {'api_detail_url': api_detail_url, 'base_template': base_template, 'computer_id': computer_id, 'ajax': ajax})

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
