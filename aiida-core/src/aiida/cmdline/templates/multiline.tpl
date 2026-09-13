{% if header %}#={{'='*72}}=#
#= {{header|wordwrap(71, wrapstring='\n#= ')}}
#={{'='*72}}=#
{% endif %}
{{value}}
{% if footer %}#={{'='*72}}=#
#= {{footer|wordwrap(71, wrapstring='\n#= ')}}
#={{'='*72}}=#
{% endif %}
