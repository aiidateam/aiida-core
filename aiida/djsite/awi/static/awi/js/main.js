/**
* main.js
* Scripts used in AiiDA Web Interface (AWI), common to all pages
* http://www.aiida.net
*/
/* We first make sure jQuery is loaded */
if (!jQuery) { throw new Error("AiiDA Web Interface requires jQuery") }

/* custom function to truncate a string after so many characters, optionally after a word, and append an ellipsis */
String.prototype.trunc =
     function(n,useWordBoundary){
         var toLong = this.length>n,
             s_ = toLong ? this.substr(0,n-1) : this;
         s_ = useWordBoundary && toLong ? s_.substr(0,s_.lastIndexOf(' ')) : s_;
         return  toLong ? s_ + '&hellip;' : s_;
      };

/**
* function that creates the pagination links, takes API parameters as an input :
* total : total number of items
* limit : items per page
* offset : first item to display in the list (0-based)
* url : base API url that was called
* previous : API url for the previous page
* next : API url for the next page
*/
function pagination(module, total, limit, offset, previous, next, ordering) {
	var output = [];
	var data_infos = 'data-ordering="'+ordering+'"';
	if(previous != null) /* if we have a previous link (i.e. not first page), we show the previous link as active */
		output.push('<li><a href="#" data-url="'+previous+'" '+data_infos+'>&laquo;</a></li>');
	else /* else we show it disabled */
		output.push('<li class="disabled"><a href="#">&laquo;</a></li>');
	for(var i=1; i <= Math.ceil(total/limit); i++) { /* create a link for each page */
		if(offset == (i-1)*limit)
			var aclass = ' class = "active"';
		else
			var aclass = '';
		if(api_urls[module].indexOf('?') == -1 && api_urls[module].indexOf('limit') == -1) /* append the selection criteria, but only if they aren't already present, also check if the order_by is already present */
			var append = '?limit='+limit+'&offset='+(i-1)*limit;
		else if(api_urls[module].indexOf('limit') == -1)
			var append = '&limit='+limit+'&offset='+(i-1)*limit;
		else
			var append = '';
		output.push('<li'+aclass+'><a href="#" data-url="'+api_urls[module]+append+'" '+data_infos+'>'+i+'</a></li>');
	}
	if(next != null) /* same as with previous link, but for next link */
		output.push('<li><a href="#" data-url="'+next+'" '+data_infos+'>&raquo;</a></li>');
	else
		output.push('<li class="disabled"><a href="#">&raquo;</a></li>');
	return output.join(""); /* return the joint string */
}

/* to close and remove a computers detail panel */
function close_detail(module, detail_id) {
	$('#'+module+'-detail-'+detail_id+' .ajax-hide').slideUp('slow', function(){
		$('#detail-'+detail_id+'>td').slideUp(function(){
			$(this).parent().remove();
		});
	});
}

/* little helper */
function nl2br(str, is_xhtml) {
	var breakTag = (is_xhtml || typeof is_xhtml === 'undefined') ? '<br />' : '<br>';
	return (str + '').replace(/([^>\r\n]?)(\r\n|\n\r|\r|\n)/g, '$1' + breakTag + '$2');
}

/* To avoid conflicts with other libraries possibly using the $ function, we isolate the code in an immediately invoked function expression */
(function($) {
	
	$(document).ready(function(){
		
	});
	
})( jQuery );