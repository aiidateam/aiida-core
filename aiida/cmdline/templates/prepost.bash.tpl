#={{'='*50}}=#
#= {{'Pre execution script'|center(48)}} =#
#={{'='*50}}=#

{{default_pre}}

{{separator}}
{{default_post}}

#={{'='*50}}=#
{{('#= Lines starting with "#=" will be ignored! Pre and post execution scripts are executed on '
   'the remote computer before and after execution of the code(s), respectively. AiiDA expects '
   'valid bash code.')|wordwrap(50, wrapstring='\n#= ')}}
#=
#={{'='*50}}=#
#= {{'Summary of config so far'|center(48)}} =#
#={{'='*50}}=#
{% for k, v in summary.items() %}#= {{k.ljust(20)}}: {{v}}
{% endfor %}
