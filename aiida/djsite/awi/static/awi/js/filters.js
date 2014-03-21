/**
* filters.js
* Scripts used for the filters of the AiiDA Web Interface (AWI)
* http://www.aiida.net
*/

function load_filters(module) {
	if($('#filters>div.btn-group').length > 0) { /* if there was already content in filters panel, remove it and show the loader */
		$('#filters>div.btn-group').remove();
		$('#filters .loader').fadeIn('fast');
	}
	$.get(modules_urls.filters[module].get, function(data){
		$('#filters>div.loader').fadeOut('fast', function(){
			$('#filters').prepend(data);
			/* load options for the new filter dropdown directly from API, disable links if filter already set */
			$('#filters-new').html('');
			$.getJSON(modules_urls.filters[module].schema, function(data){
				$.each(data.fields, function(k, o){
					if(o.hasOwnProperty('filtering')) {
						if($('#filters #filter-'+k).length == 0) {
							$('#filters-new').append('<li><a href="'+modules_urls.filters[module].create.substring(0, modules_urls.filters[module].create.length - 1)+k+'" data-toggle="modal" data-target="#filter-modal">'+o.display_name+'</a></li>');
						}
						else {
							$('#filters-new').append('<li class="disabled"><a href="#">'+o.display_name+'</a></li>');
						}
					}
				});
			});
		});
	});
}

/* To avoid conflicts with other libraries possibly using the $ function, we isolate the code in an immediately invoked function expression */
(function($) {
	
	$(document).ready(function(){
		/* ajax to get the filters */
		load_filters(module); /* module is defined in the dedicated js file for the module */
		
		/* listen for the delete filter links */
		$('#filters').delegate('button.filter-remove', 'click', function(e){
			e.preventDefault(); /* we do not want the empty anchor to bring us back to the top of the page */
			var me = $(this);
			var field = me.attr('data-field');
			/* ajax to delete filter */
			$.ajax({
				url: modules_urls.filters[module].remove.substring(0, modules_urls.filters[module].remove.length - 1)+field,
				type: 'GET',
				success: function(data) {
					load_filters(module); /* if everything ok */
					window['load_'+module](false, $('#'+module+'-list').attr('data-ordering'));
				},
				error: function(xhr, status, error) {
					$('body>div.container').prepend('<div class="alert alert-danger"><strong>Oops</strong>, '+
						'there was a problem. Could not change operator on filter "'+field+'" : '+xhr.responseText+'</div>');
				}
			});
		});
		
		/* listen for operator changes in dropdowns */
		$('#filters').delegate('a.filter-change-operator', 'click', function(e){
			e.preventDefault(); /* we do not want the empty anchor to bring us back to the top of the page */
			var me = $(this);
			var field = me.attr('data-field');
			var operator = me.attr('data-operator');
			/* ajax to change the operator */
			$.ajax({
				url: modules_urls.filters[module].set.substring(0, modules_urls.filters[module].set.length - 1)+field,
				type: 'POST',
				data: {'operator': operator},
				success: function(data) {
					load_filters(module); /* if everything ok */
					window['load_'+module](false, $('#'+module+'-list').attr('data-ordering'));
				},
				error: function(xhr, status, error) {
					$('body>div.container').prepend('<div class="alert alert-danger"><strong>Oops</strong>, '+
						'there was a problem. Could not change operator on filter "'+field+'" : '+xhr.responseText+'</div>');
				}
			});
		});
		
		/* listen for value changes in dropdowns for list-type filters */
		$('#filters').delegate('a.filter-change-value', 'click', function(e){
			e.preventDefault(); /* we do not want the empty anchor to bring us back to the top of the page */
			var me = $(this);
			var field = me.attr('data-field');
			var value = me.text();
			/* ajax to change the operator */
			$.ajax({
				url: modules_urls.filters[module].set.substring(0, modules_urls.filters[module].set.length - 1)+field,
				type: 'POST',
				data: {'value': value},
				success: function(data) {
					load_filters(module); /* if everything ok */
					window['load_'+module](false, $('#'+module+'-list').attr('data-ordering'));
				},
				error: function(xhr, status, error) {
					$('body>div.container').prepend('<div class="alert alert-danger"><strong>Oops</strong>, '
						+'there was a problem. Could not change value on filter "'+field+'" : '+xhr.responseText+'</div>');
				}
			});
		});
		
		/* the modal size needs to change depending on the displayed content : small for value changes but normal for creating new filters */
		$('#filters-new').delegate('a', 'click', function(){
			$('#filter-modal .modal-dialog').removeClass('modal-sm');
		});
		$('#filters').delegate('button.filter-value', 'click', function(){
			$('#filter-modal .modal-dialog').addClass('modal-sm');
		});
	});
	
})( jQuery );