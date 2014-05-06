function ComputersManager(ApplicationManager) {
	this.applicationManager = ApplicationManager;
	this.module = 'computers';
	this.moduleS = 'computer';
	this.columns = 8; // number of columns in the listing table
	this.loadUrl = modules_urls[this.module].listing;
	this.filterUrls = modules_urls.filters[this.module];
	this.table = $('#' + this.module + '-list');
	this.pagination = $('#' + this.module + '-pag');
	this.modalId = this.moduleS + '-modal';
	this.modal = $('#' + this.modalId);
	this.ordering = this.table.attr('data-ordering') || 'id';
	
	this.listen();
	this.load(false);
}

// listen for click events on buttons and links
ComputersManager.prototype.listen = function () {
	var self = this;
	
	// 'details' link, show the details on a row below
	this.table.delegate('a.show-detail', 'click', function (e) {
		e.preventDefault();
		var id = $(this).attr('data-id');
		var url = $(this).attr('href');
		self.toggleDetails(id, url, $(this));	
	});
	
	// close 'details' panel
	this.table.delegate('.detail-close>button', 'click', function (e) {
		e.preventDefault();
		var id = $(this).attr('data-id');
		self.closeDetails(id);
	});
	
	// 'disable' links
	this.table.delegate('a.computer-disable', 'click', function (e) {
		e.preventDefault();
		var url = $(this).attr('href');
		var id = $(this).attr('data-id');
		self.disable(id, url);
	});
	
	// 'enable' links
	this.table.delegate('a.computer-enable', 'click', function (e) {
		e.preventDefault();
		var url = $(this).attr('href');
		var id = $(this).attr('data-id');
		self.enable(id, url);
	});
	
	// 'delete' links
	this.table.delegate('a.computer-delete', 'click', function (e) {
		e.preventDefault();
		var id = $(this).attr('data-id');
		if (confirm('Are you sure you want to delete computer ' + id + '?')) {
			var url = $(this).attr('href');
			self.delete(id, url);
		}
	});
};

// toggle the details panel for a computer
ComputersManager.prototype.toggleDetails = function (id, url, trigger) {
	var self = this;
	
	// we check if the panel is already open
	if ($('#detail-' + id).length > 0) {
		self.closeDetails(id);
	} else {
		self.openDetails(id, url, trigger);
	}
};

// close details of a computer
ComputersManager.prototype.closeDetails = function (id) {
	$('#' + this.module + '-detail-' + id + ' .ajax-hide').slideUp('slow', function () {
		$('#detail-' + id + '>td').slideUp(function () {
			$(this).parent().remove();
			$('#row-' + id + '>td.name>a>span').removeClass('caret').addClass('right-caret');
		});
	});
};

// open details of a computer
ComputersManager.prototype.openDetails = function (id, url, trigger) {
	var self = this;
	
	$('#row-' + id + '>td.name>a>span').removeClass('right-caret').addClass('caret');
	trigger.closest('tr').after('<tr id="detail-' + id + '" class="loader detail"><td colspan="' + self.columns + '">' +
		'<div class="dots">Loading...</div></td></tr>');
	$('tr#detail-' + id + '>td').slideDown(function () {
		var td = $(this);
		$.get(url, function (data) {
			td.prepend(data);
		}); 
	})
};

// disable computer
ComputersManager.prototype.disable = function (id, url) {
	var self = this;
	
	$.ajax({
		url: url,
		type: 'PATCH',
		dataType: 'json',
		contentType: 'application/json',
		processData: false,
		data: '{"enabled":false}',
		success: function (data) {
			$('#row-' + id + '>td.status').html('<span class="label label-danger">false</span>');
			$('#row-' + id + ' ul.dropdown-menu>li.status>a').removeClass('computer-disable')
				.addClass('computer-enable').html('<span class="glyphicon glyphicon-ok"></span>&nbsp;&nbsp;Enable');
		},
		error: function (xhr, status, error) { /* or we show an error message */
			self.errorMessage('disable', id, $.parseJSON(xhr.responseText).dbcomputer.enabled);
		}
	});
};

// enable computer
ComputersManager.prototype.enable = function (id, url) {
	var self = this;
	
	$.ajax({
		url: url,
		type: 'PATCH',
		dataType: 'json',
		contentType: 'application/json',
		processData: false,
		data: '{"enabled":true}',
		success: function (data) {
			$('#row-' + id + '>td.status').html('<span class="label label-success">true</span>');
			$('#row-' + id + ' ul.dropdown-menu>li.status>a')
				.removeClass('computer-enable')
				.addClass('computer-disable')
				.html('<span class="glyphicon glyphicon-ban-circle"></span>&nbsp;&nbsp;Disable');
		},
		error: function (xhr, status, error) { /* or we show an error message */
			self.errorMessage('enable', id, $.parseJSON(xhr.responseText).dbcomputer.enabled);
		}
	});
};

// delete computer
ComputersManager.prototype.delete = function (id, url) {
	var self = this;
	
	$.ajax({
		url: url,
		type: 'DELETE',
		dataType: 'json',
		contentType: 'application/json',
		processData: false,
		success: function (data) {
			self.load(true); // reload list
		},
		error: function (xhr, status, error) { /* or we show an error message */
			try {
				var errorText = $.parseJSON(xhr.responseText);
			} catch (e) {
				var errorText = xhr.responseText;
			}
			if (errorText.constructor === Object) {
				var errors = [];
				$.each(errorText.dbcomputer, function (k, v) {
					errors.push(errorText.dbcomputer[k]);
				});
				errorText = errors.join(', ');
			}
			self.errorMessage('delete', id, errorText);
		}
	});
};

// load the markup for the listing table
ComputersManager.prototype.load = function (scroll) {
	var self = this;
	
	if (scroll == undefined)
		scroll = false;
	// if there was already content in the table, remove it and show the loader
	if (this.table.children('tr').length > 1) {
		this.table.children('tr').filter(':visible').remove();
		this.table.find('.loader').fadeIn('fast');
	}
	if (this.loadUrl.indexOf('?') == -1 && this.loadUrl.indexOf('order_by') == -1)
		this.loadUrl += '?order_by=' + this.ordering;
	else if (this.loadUrl.indexOf('order_by') == -1)
		this.loadUrl += '&order_by=' + this.ordering;
	
	// get the querystring
	$.get(this.filterUrls.querystring, function (qs) {
		var apiurl = self.loadUrl + qs;
		$.getJSON(apiurl, function (data) {
			var rows = [];
			// used to show colored labels for activation status
			var enabled = {
				true: '<span class="label label-success">true</span>',
				false: '<span class="label label-danger">false</span>'
			}
			
			var next = function () {
				if (rows.length == 0) {
					rows.push('<tr><td colspan="' + self.columns + '" class="center">No matching entry</td></tr>');
				}
				self.table.find('.loader').fadeOut('fast', function () {
					self.table.append(rows.join(""));
					self.table.find('span').tooltip(); // activate the tooltips
					if (scroll) {
						$('html, body').animate({
							scrollTop: self.table.parent().offset().top-50
						}, 200);
					}
				});
			};
			
			// for each computer, we build the html of a table row
			$.each(data.objects, function (k, o) {
				rows.push(''); // reserve a spot in the output for this row
				// we update the corresponding line, this ensures that data is gonna be displayed in the right order at the end
				rows[k] = '<tr id="row-' + o.id + '">' +
					'<td>' + o.id + '</td>' +
					'<td class="name"><a href="' + self.getUrl('detail') + o.id + '" class="show-detail" data-id="' + o.id +
					'"><strong>' + o.name + '</strong>&nbsp;<span class="right-caret"></span></a></td>' +
					'<td>' + o.description.trunc(30, true, true) + '</td>' + /* description is truncated via this custom function */
					'<td class="transport_type">' + o.transport_type + '</td>' +
					'<td>' + o.hostname + '</td>' +
					'<td class="scheduler_type">' + o.scheduler_type + '</td>' +
					'<td class="status">' + enabled[o.enabled] + '</td>' +
					'<td>' +
						'<div class="btn-group">' + /* actions dropdown */
							'<button type="button" class="btn btn-primary btn-sm dropdown-toggle" data-toggle="dropdown">' +
								'Action <span class="caret"></span>' +
							'</button>' +
							'<ul class="dropdown-menu dropdown-menu-right" role="menu">' +
								'<li><a href="' + self.getUrl('detail') + o.id + '" class="show-detail"' +
									'data-id="' + o.id + '"><span class="glyphicon glyphicon-tasks"></span>&nbsp;&nbsp;Details</a></li>' +
									(o.enabled == true	?
										'<li class="status"><a href="' + o.resource_uri + '" class="computer-disable" data-id="' + o.id + '"><span class="glyphicon glyphicon-ban-circle"></span>&nbsp;&nbsp;Disable</a></li>'
										: '<li class="status"><a href="' + o.resource_uri + '" class="computer-enable" data-id="' + o.id + '"><span class="glyphicon glyphicon-ok"></span>&nbsp;&nbsp;Enable</a></li>') +
								'<li><a href="' + self.getUrl('edit') + o.id + '" data-toggle="modal" data-target="#' + self.modalId + '">' +
									'<span class="glyphicon glyphicon-pencil"></span>&nbsp;&nbsp;Edit</a></li>' +
								'<li><a href="' + o.resource_uri + '" class="computer-delete text-danger" data-id="' + o.id + '"><span class="glyphicon glyphicon-remove-circle"></span>&nbsp;&nbsp;Delete</a></li>' +
							'</ul>' +
						'</div>' +
					'</td>' +
				'</tr>';
				if (k == data.objects.length - 1) {
					next();
				}
			});
			
			if (rows.length == 0) {
				next();
			}
			/*
			var timer = function () {
				if (rows.length == data.objects.length && (rows.length == 0 || rows[0] != '')) {
					if (rows.length == 0) {
						rows.push('<tr><td colspan="' + self.columns + '" class="center">No matching entry</td></tr>');
					}
					self.table.find('.loader').fadeOut('fast', function () {
						self.table.append(rows.join(""));
						self.table.find('span').tooltip();
						if (scroll) {
							$('html, body').animate({
								scrollTop: self.table.parent().offset().top-50
							}, 200);
						}
					});
				} else {
					window.setTimeout(timer, 100);
				}
			};
			timer();
			*/
			self.pagination.hide().html( /* load the pagination via this custom function */
				self.applicationManager.pagination(
					data.meta.total_count,
					data.meta.limit,
					data.meta.offset,
					data.meta.previous,
					data.meta.next
				)
			).fadeIn();
		});
	});
	// we add the required modal somewhere in the body where it isn't affected by css
	this.modal = this.modal.refresh();
	if (this.modal.length == 0) {
		$('body>div.container').prepend('<div class="modal fade" id="' + this.modalId + '" tabindex="-1" role="dialog" aria-hidden="true">' +
		'<div class="modal-dialog">' +
				'<div class="modal-content">' +
				'</div>' +
			'</div>' +
		'</div>');
		// we need to delete the bs.modal instance upon closing it otherwise the content doesn't get updated next time we open the modal with a remote url
		$('body').on('hidden.bs.modal', '#' + this.modalId, function () {
			$(this).removeData('bs.modal');
		});
	}
};

ComputersManager.prototype.loadDetail = function (url, id) {
	var self = this;
	
	$.getJSON(url, function (data) {
		$.getJSON(self.getAPIUrl('authinfo') + '?dbcomputer=' + id, function (subdata) {
			var ajaxLoaded = 0;
		
			var loader = $('#' + self.module + '-detail-' + id + ' ~ .dots');
			var rows = [
				'<div class="ajax-hide">',
				'<ul class="media-list">',
				'<li class="media"><strong class="pull-left">Users</strong><div class="media-body">'
			];
			
			var users = [];
			$.each(subdata.objects, function (k, v) {
				users.push(v.aiidauser.username);
			});
			if (users.length === 0) {
				users.push('This computer is not configured for your user.');
			}
			rows.push(users.join(', '));
			
			rows.push(
				'</div></li>',
				'<li class="media"><strong class="pull-left">Description</strong><div class="media-body">' + data.description + '</div></li>',
				'<li class="media"><strong class="pull-left">Metadata</strong><div class="media-body"><ul class="media-list">'
			);
		
			$.each(data.metadata, function (k, v) { /* we go over all metadatas and display them in a nested way */
				if (v instanceof Array) {
					var metaValue = ['<ul>'];
					$.each(v, function (key, val) {
						metaValue.push('<li>' + val + '</li>');
					});
					var value = metaValue.join('');
				}
				else
					var value = nl2br(v);
				rows.push('<li class="media"><strong class="pull-left">' + k.trunc(18, false, true) + '</strong><div class="media-body">' + value + '</div></li>');
			});
			rows.push(
				'</ul></div></li>',
				'<li class="media"><strong class="pull-left">Transport parameters</strong><div class="media-body"><ul class="media-list">'
			);
			$.each(data.transport_params, function (k, v) { /* we go over all transport parameters and display them in a nested way */
				if (v instanceof Array)
					var value = v.join('<br>');
				else
					var value = nl2br(v);
				rows.push('<li class="media"><strong class="pull-left">' + k.trunc(18, false, true) + '</strong><div class="media-body">' + value + '</div></li>');
			});
			rows.push(
				'</ul></div></li>',
				'<li class="media"><strong class="pull-left">UUID</strong><div class="media-body">' + data.uuid + '</div></li>',
				'</ul></div>'
			);
			var next = function () {
				loader.fadeTo('fast', 0.01, function () { /* we hide the loader and show the details html */
					$('#' + self.module + '-detail-' + id).prepend(rows.join(''));
					$('#' + self.module + '-detail-' + id + ' .ajax-hide').slideDown(function () {
						loader.hide();
						$('#' + self.module + '-detail-' + id + '>.detail-close').fadeIn();
					});
					$('#' + self.module + '-detail-' + id).find('span').tooltip();
				});
			};
			next();
		});
	});
};

ComputersManager.prototype.loadEdit = function (id) {
	var self = this;
	this.modal = this.modal.refresh();
	
	// get possible values for transport type and scheduler type and populate the dropdowns
	var transportfield = this.modal.find('select#computer-transport');
	var schedulerfield = this.modal.find('select#computer-scheduler');
	$.getJSON(self.getUrl('schema'), function (data) {
		transportfield.html(function () {
			var content = [];
			for (var v in data.fields.transport_type.valid_choices) {
				if (v == $('#row-' + id + '>td.transport_type').text()) {
					content.push('<option value="' + v + '" selected="selected">' + v + '</option>');
				} else {
					content.push('<option value="' + v + '">' + v + '</option>');
				}
			}
			return content.join('');
		});
		schedulerfield.html(function () {
			var content = [];
			for (var v in data.fields.scheduler_type.valid_choices) {
				if (v == $('#row-' + id + '>td.scheduler_type').text()) {
					content.push('<option value="' + v + '" selected="selected">' + v + '</option>');
				} else {
					content.push('<option value="' + v + '">' + v + '</option>');
				}
			}
			return content.join('');
		});
	});
	
	var namefield = this.modal.find('input#computer-name');
	namefield.val($('#row-' + id + '>td.name strong').text());
	window.setTimeout(function () {
		// we focus on the input field when the animation is over (just required for the first load, is then handled by the event show.bs.modal)
		namefield.select().focus();
	}, 500);
	this.modal.find('button.computer-submit').click(function () {
		$.ajax({
			url: self.getUrl('apidetail') + id + '/',
			type: 'PATCH',
			dataType: 'json',
			contentType: 'application/json',
			processData: false,
			data: '{"name":"' + namefield.val() + '",' +
				'"transport_type":"' + self.modal.find('select#computer-transport>option:selected').val() + '",' +
				'"scheduler_type":"' + self.modal.find('select#computer-scheduler>option:selected').val() + '"}',
			success: function (data) {
				self.modal.modal('toggle');
				$('#row-' + id + '>td.name strong').text(data.name);
				$('#row-' + id + '>td.transport_type').text(data.transport_type);
				$('#row-' + id + '>td.scheduler_type').text(data.scheduler_type);
			},
			error: function (xhr, status, error) {
				$.each($.parseJSON(xhr.responseText).dbcomputer, function (k, v) {
					self.errorModal(k, $.parseJSON(xhr.responseText).dbcomputer[k]);
				});
			}
		});
	});
	// on pressing the enter key, trigger the click event on the button (submit)
	this.modal.find('input.form-control').keypress(function (event) {
		if (event.which == 13) {
			self.modal.find('button.computer-submit').click();
		}
	});
	// after apparition animation is complete, focus on the field
	this.modal.on('shown.bs.modal', function (e) {
		namefield.select().focus();
	});
	// if there was an error message, hide it on modal apparition
	this.modal.on('show.bs.modal', function (e) {
		self.modal.find('input').parent().removeClass('has-error');
		self.modal.find('.alert').html('').hide();
	});
};

// get ajax url for a function
ComputersManager.prototype.getUrl = function (action) {
	var url = modules_urls[this.module][action];
	if (url.slice(-2) == '/0') {
		return url.substring(0, url.length - 1);
	} else if (url.slice(-3) == '/0/') {
		return url.substring(0, url.length - 2);
	} else {
		return url;
	}
};
// get ajax api url
ComputersManager.prototype.getAPIUrl = function (resource) {
	var url = api_urls[resource];
	if (url.slice(-2) == '/0') {
		return url.substring(0, url.length - 1);
	} else if (url.slice(-3) == '/0/') {
		return url.substring(0, url.length - 2);
	} else {
		return url;
	}
};

// add an error message to the page DOM
ComputersManager.prototype.errorMessage = function (action, id, error) {
	var message = {
		disable: 'Could not disable computer ' + id,
		enable: 'Could not enable computer ' + id,
		delete: 'Could not delete computer ' + id
	}
	$('body>div.container').prepend('<div class="alert alert-danger"><strong>Oops</strong>, there was a problem. ' +
		message[action] + ': ' + error + '</div>');
};

// add an error message to the modal box
ComputersManager.prototype.errorModal = function (field, error) {
	var fieldElem = this.modal.find('input#computer-' + field);
	this.modal.find('.alert').append('<strong>Oops</strong>, there was a problem: ' + error + '<br>')
		.show();
	fieldElem.parent().addClass('has-error');
	fieldElem.select().focus();
};

