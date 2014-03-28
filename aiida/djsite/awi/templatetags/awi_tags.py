from django import template
from django.utils.datastructures import SortedDict
from django.core import urlresolvers

register = template.Library()

@register.simple_tag(takes_context=True)
def current(context, url_name, return_value=' active', **kwargs):
	"""
    Return the 'active' class if a page is the one that is being visited at the moment (to highlight in the navbar)
    """
	matches = current_url_equals(context, url_name, **kwargs)
	return return_value if matches else ''

def current_url_equals(context, url_name, **kwargs):
	"""
    Internal function to compare the given url expression with the actual visited page
    """
	resolved = False
	try:
		resolved = urlresolvers.resolve(context.get('request').path)
	except:
		pass
	matches = resolved and resolved.url_name == url_name
	if matches and kwargs:
		for key in kwargs:
			kwarg = kwargs.get(key)
			resolved_kwarg = resolved.kwargs.get(key)
			if not resolved_kwarg or kwarg != resolved_kwarg:
				return False
	return matches

@register.filter(name='sort', is_safe=True)
def listsort(value):
	"""
	Allows to sort dictionaries on the fly when doing a for loop over their items
	"""
	if isinstance(value, dict):
		new_dict = SortedDict()
		key_list = value.keys()
		key_list.sort()
		for key in key_list:
			new_dict[key] = value[key]
		return new_dict
	elif isinstance(value, list):
		new_list = list(value)
		new_list.sort()
		return new_list
	else:
		return value
