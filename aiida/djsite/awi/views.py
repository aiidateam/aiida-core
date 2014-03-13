from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

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

# Computers page view
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

@login_required(login_url='awi:login')
def computers_rename(request, computer_id):
	"""
	Rename form for computers
	"""
	return render(request, 'awi/computers_rename.html', {'computer_id': computer_id})

@login_required(login_url='awi:login')
def filters_value(request, field):
	"""
	Update value form for filters
	"""
	return render(request, 'awi/filters_value.html', {'field': field})

def codes(request):
	"""
	Codes page view
	"""
	return render(request, 'awi/base_codes.html')
