{{'*'*width}}
|{{' '*(width-2)}}|
| {{'WARNING!'|center(width-4)}} |
{% for line in msg %}| {{line|center(width-4)}} |
{% endfor %}|{{' '*(width-2)}}|
{{'*'*width}}
