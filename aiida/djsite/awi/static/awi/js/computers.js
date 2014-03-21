/**
* computers.js
* Scripts used in the computers module of the AiiDA Web Interface (AWI)
* http://www.aiida.net
*/

var module = 'computers';
var module_s = 'computer';

/**
* this function loads the computers list in a table, takes as input the API url,
* details URL (for a computer), rename url, if it should scroll to the top of the table after loading or not,
* and the ordering criterion
*/
function load_computers(scroll, ordering) {
	if(scroll == undefined)
		scroll = false;
	if(ordering == undefined) /* default ordering field */
		ordering = 'id';
	if($('#'+module+'-list>tr').length > 1) { /* if there was already content in the table, remove it and show the loader, also remove the modal boxes */
		$('#'+module+'-list>tr').filter(':visible').remove();
		$('div.rename-modal').remove();
		$('#'+module+'-list .loader').fadeIn('fast');
	}
	if(api_urls[module].indexOf('?') == -1 && api_urls[module].indexOf('order_by') == -1)
		api_urls[module] += '?order_by='+ordering;
	else if(api_urls[module].indexOf('order_by') == -1)
		api_urls[module] += '&order_by='+ordering;
	/* get the query string */
	$.get(modules_urls.filters[module].querystring, function(qs){
		var apiurl = api_urls[module] + qs;
		$.getJSON(apiurl, function(data){ /* get the json via API */
			var rows = [];
			var status = {/* used to show colored labels for activation status */
				true: '<span class="label label-success">enabled</span>',
				false: '<span class="label label-danger">disabled</span>'
			}
			$.each(data.objects, function(k, o){ /* for each computer, we build the html of a table row */
				$('body>div.container').prepend('<div class="modal fade rename-modal" id="modal-'+o.id+'" role="dialog" aria-labelledby="renameLabel'+o.id+'" aria-hidden="true" tabindex="-1" data-rename="'+o.name+'" data-url="'+o.resource_uri+'">'+
					'<div class="modal-dialog modal-sm">'+
					'<div class="modal-content">'+
					'</div></div></div>'); /* we prepare a modal box for each */
				rows.push(''); /* we reserve a spot in the output for this line */
				$.getJSON(api_urls.authinfo+'?computer='+o.id, function(subdata) { /* get the user infos, api_authinfo_url is defined in a script in the base.html template */
					var username = subdata.objects[0].aiidauser.username; /* user data is included in the authinfo api response */
					rows[k] = '<tr id="row-'+o.id+'">'+ /* we update the corresponding line, this ensures that data is gonna be displayed in the right order at the end */
						'<td>'+o.id+'</td>'+
						'<td class="name"><strong>'+o.name+'</strong><a href="'+modules_urls[module].detail.substring(0, modules_urls[module].detail.length - 1)+o.id+'" class="show-detail" data-id="'+o.id+'">&nbsp;<span class="right-caret"></span></a></td>'+
						'<td><span title="'+o.description+'" data-toggle="tooltip">'+o.description.trunc(30,true)+'</span></td>'+ /* description is truncated via this custom function */
						'<td>'+username+'</td>'+
						'<td>'+o.transport_type+'</td>'+
						'<td>'+o.hostname+'</td>'+
						'<td>'+o.scheduler_type+'</td>'+
						'<td class="status">'+status[o.enabled]+'</td>'+
						'<td>'+
							'<div class="btn-group">'+ /* actions dropdown */
								'<button type="button" class="btn btn-primary btn-sm dropdown-toggle" data-toggle="dropdown">'+
									'Action <span class="caret"></span>'+
								'</button>'+
								'<ul class="dropdown-menu dropdown-menu-right" role="menu">'+
									'<li><a href="'+modules_urls[module].detail.substring(0, modules_urls[module].detail.length - 1)+o.id+'" class="show-detail"'+
										'data-id="'+o.id+'"><span class="glyphicon glyphicon-tasks"></span>&nbsp;&nbsp;Details</a></li>'+
									(o.enabled == true ? '<li class="status"><a href="'+o.resource_uri+'" class="computer-disable" data-id="'+o.id+'"><span class="glyphicon glyphicon-ban-circle"></span>&nbsp;&nbsp;Disable</a></li>'
										: '<li class="status"><a href="'+o.resource_uri+'" class="computer-enable" data-id="'+o.id+'"><span class="glyphicon glyphicon-ok"></span>&nbsp;&nbsp;Enable</a></li>')+
									'<li><a href="'+modules_urls[module].rename.substring(0, modules_urls[module].rename.length - 1)+o.id+'" data-toggle="modal" data-target="#modal-'+o.id+'">'+
										'<span class="glyphicon glyphicon-pencil"></span>&nbsp;&nbsp;Rename</a></li>'+
									'<li class="disabled"><a href="#"><span class="glyphicon glyphicon-cog"></span>&nbsp;&nbsp;Configure</a></li>'+
									'<li class="disabled"><a href="#" class="text-danger"><span class="glyphicon glyphicon-remove-circle"></span>&nbsp;&nbsp;Delete</a></li>'+
								'</ul>'+
							'</div>'+
						'</td>'+
					'</tr>';
				});
			});
			/* we need to wait until all ajax data is loaded */
			var computers_timer = function() { /* this is a timer function to defer code execution */
				if (rows.length == data.objects.length && (rows.length == 0 || rows[0] != '')) { /* if all secondary data is loaded */
					if(rows.length == 0) {
						rows.push('<tr><td colspan="9" class="center">No matching entry</td></tr>');
					}
					$('#computers-list .loader').fadeOut('fast', function(){ /* fade out the loader and add all table rows */
						$('#computers-list').append(rows.join(""));
						$('#computers-list span').tooltip(); /* activate the tooltips */
						if(scroll) { /* if we chose to scroll to the top of the table, then do so */
							$('html, body').animate({scrollTop: $("#computers-list").parent().offset().top-50}, 200);
						}
					});
				} else { /* otherwise we defer for 100 milliseconds */
					window.setTimeout(computers_timer, 100);
				}
			};
			computers_timer();
			$('#computers-pag').hide().html( /* load the pagination via this custom function */
				pagination(module,
					data.meta.total_count,
					data.meta.limit,
					data.meta.offset,
					data.meta.previous,
					data.meta.next,
					ordering
				)
			).fadeIn();
		});
	});
}

/* To avoid conflicts with other libraries possibly using the $ function, we isolate the code in an immediately invoked function expression */
(function($) {
	$(document).ready(function(){ /* actions to perform at page load and definition of event listeners */
		load_computers(false, $('#computers-list').attr('data-ordering'));  /* load the first page of computers */
	
		/* listen for click events on the pagination links */
		$('#computers-pag').delegate('a', 'click', function(e){
			e.preventDefault(); /* we do not want the empty anchor to bring us back to the top of the page */
			var me = $(this);
			if(me.parent().hasClass('disabled')) { /* check if the link was disabled */
				return false;
			}
			else {
				api_urls.computers = me.attr('data-url');
				load_computers(true, me.attr('data-ordering')); /* load the new list with this new API url, true to scroll to the beginning of the table after loading */
			}
		});
	
		/* when clicking the 'details' link, show the details on a row below */
		$('#computers-list').delegate('a.show-detail', 'click', function(e){
			e.preventDefault(); /* we do not want to go to the detail page */
			var me = $(this);
			var detail_id = me.attr('data-id'); /* this is the computer id */
			if($('#detail-'+detail_id).length > 0) { /* we check if the panel is already open */
				close_detail(module, detail_id);
				$('#row-'+detail_id+'>td.name>a>span').removeClass('caret').addClass('right-caret');
			}
			else {
				$('#row-'+detail_id+'>td.name>a>span').removeClass('right-caret').addClass('caret');
				var detail_url = me.attr('href'); /* this is the details page url */
				me.closest('tr').after('<tr id="detail-'+detail_id+'" class="loader detail"><td colspan="9">'+
					'<div class="dots">Loading...</div></td></tr>'); /* add the required line (hidden) */
				$('tr#detail-'+detail_id+'>td').slideDown(function(){ /* show it */
					var td = $(this);
					$.get(detail_url, function(data){ /* and load the content */
						td.prepend(data);
					}); 
				})
			}	
		});
		/* listen to the "disable" links */
		$('#computers-list').delegate('a.computer-disable', 'click', function(e){
			e.preventDefault(); /* we do not want to go to the api url */
			var me = $(this);
			var api_url = me.attr('href');
			var computer_id = me.attr('data-id');
			$.ajax({ /* call the api with the required data */
				url: api_url,
				type: 'PATCH',
				dataType: 'json',
				contentType: 'application/json',
				processData: false,
				data: '{"enabled":false}',
				success: function(data) { /* on success, we change the label in the table row and change the link in the actions dropdown */
					$('#row-'+computer_id+'>td.status').html('<span class="label label-danger">disabled</span>');
					$('#row-'+computer_id+' ul.dropdown-menu>li.status>a').removeClass('computer-disable').addClass('computer-enable').html('<span class="glyphicon glyphicon-ok"></span>&nbsp;&nbsp;Enable');
				},
				error: function(xhr, status, error){ /* or we show an error message */
					$('body>div.container').prepend('<div class="alert alert-danger"><strong>Oops</strong>, there was a problem. Could not change status on computer '+computer_id+' : '+$.parseJSON(xhr.responseText).dbcomputer.enabled+'</div>');
				}
			});
		});
		/* listen to the "enable" links */
		$('#computers-list').delegate('a.computer-enable', 'click', function(e){
			e.preventDefault(); /* we do not want to go to the api url */
			var me = $(this);
			var api_url = me.attr('href');
			var computer_id = me.attr('data-id');
			$.ajax({ /* call the api with the required data */
				url: api_url,
				type: 'PATCH',
				dataType: 'json',
				contentType: 'application/json',
				processData: false,
				data: '{"enabled":true}',
				success: function(data) { /* on success, we change the label in the table row and change the link in the actions dropdown */
					$('#row-'+computer_id+'>td.status').html('<span class="label label-success">enabled</span>');
					$('#row-'+computer_id+' ul.dropdown-menu>li.status>a').removeClass('computer-enable').addClass('computer-disable').html('<span class="glyphicon glyphicon-ban-circle"></span>&nbsp;&nbsp;Disable');
				},
				error: function(xhr, status, error){ /* or we show an error message */
					$('body>div.container').prepend('<div class="alert alert-danger"><strong>Oops</strong>, there was a problem. Could not change status on computer '+computer_id+' : '+$.parseJSON(xhr.responseText).dbcomputer.enabled+'</div>');
				}
			});
		});
	});
})( jQuery );
