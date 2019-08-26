{% for title, message in header.items() %}#{{' {} '.format(title).center(width - 2, '=')}}#
#{{' '*(width - 2)}}#
{% for line in message %}# {{line.ljust(width - 4)}} #
{% endfor %}#{{' '*(width - 2)}}#
{% endfor %}{% if debug %}#{{' !!! DEBUG MODE !!! '.center(width - 2, '=')}}#{% else %}#{{'='*(width - 2)}}#{% endif %}
