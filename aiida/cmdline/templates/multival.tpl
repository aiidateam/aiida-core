{% for title, defaults in docs %}
#={{'='*50}}=#
#= {{title|center(48)}} =#
#={{'='*50}}=#

{{defaults}}

{% endfor %}
#={{'='*50}}=#
{{'#= ' + helpmsg|wordwrap(50, wrapstring='\n#= ')}}
