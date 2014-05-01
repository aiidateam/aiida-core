function CalculationsManager(ApplicationManager) {
	this.applicationManager = ApplicationManager;
	this.module = 'calculations';
	this.moduleS = 'calculation';
	this.columns = 6; // number of columns in the listing table
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
CalculationsManager.prototype.listen = function () {
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
};

// toggle the details panel for a calculation
CalculationsManager.prototype.toggleDetails = function (id, url, trigger) {
	var self = this;
	
	// we check if the panel is already open
	if ($('#detail-' + id).length > 0) {
		self.closeDetails(id);
	} else {
		self.openDetails(id, url, trigger);
	}
};

// close details of a calculation
CalculationsManager.prototype.closeDetails = function (id) {
	$('#' + this.module + '-detail-' + id + ' .ajax-hide').slideUp('slow', function () {
		$('#detail-' + id + '>td').slideUp(function () {
			$(this).parent().remove();
			$('#row-' + id + '>td.name>a>span').removeClass('caret').addClass('right-caret');
		});
	});
};

// open details of a calculation
CalculationsManager.prototype.openDetails = function (id, url, trigger) {
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

// load the markup for the listing table
CalculationsManager.prototype.load = function (scroll) {
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
			// for each calculation, we build the html of a table row
			$.each(data.objects, function (k, o) {
				rows.push(''); // reserve a spot in the output for this row
				
				// http://localhost:8000/api/v1/attribute/?id__in=23&id__in=26&id__in=27&id__in=28&id__in=29&id__in=75&id__in=78&id__in=80&id__in=81&id__in=82&id__in=83&key=state
				// http://localhost:8000/api/v1/attribute/?id__in=23,26,27,28,29,75,78,80,81,82,83&key=state
				var stateUrl = self.getAPIUrl('attributes') + '?';
				/*var attrIds = [];
				for (var i = 0, len = o.attributes.length; i < len; i++) {
					attrIds.push(o.attributes[i].substring(0, o.attributes[i].length - 1).split('/').pop());
				}
				stateUrl = stateUrl + attrIds.join(',');
				stateUrl = stateUrl + '&key=state';*/
				
				$.getJSON(o.dbcomputer, function (subsubdata) {
					var computername = subsubdata.name;
					//var ctime = new Date((o.ctime || "").replace(/-/g,"/").replace(/[TZ]/g," "));
					var ctime = new Date();
					ctime.setISO8601(o.ctime);
					
					if (o.class_name == 'None') {
						o.class_name = '<span class="text-danger">Error</span>';
					} else if (o.class_name === undefined || o.class_name == '') {
						o.class_name = o.base_class;
					}
					
					// we update the corresponding line, this ensures that data is gonna be displayed in the right order at the end
					rows[k] = '<tr id="row-' + o.id + '">' +
						'<td>' + o.id + '</td>' +
						'<td class="name"><a href="' + self.getUrl('detail') + o.id + '" class="show-detail" data-id="' + o.id +
						'"><strong>' + o.label + '</strong>&nbsp;<span class="right-caret"></span></a></td>' +
						'<td><span title="' + o.type + '" data-toggle="tooltip">' + o.class_name + '</span></td>' +
						'<td>' + computername + '</td>' +
						'<td>' + ctime.toLocaleString() + '</td>' +
						'<td>' +
							'<div class="btn-group">' + /* actions dropdown */
								'<button type="button" class="btn btn-primary btn-sm dropdown-toggle" data-toggle="dropdown">' +
									'Action <span class="caret"></span>' +
								'</button>' +
								'<ul class="dropdown-menu dropdown-menu-right" role="menu">' +
									'<li><a href="' + self.getUrl('detail') + o.id + '" class="show-detail"' +
										'data-id="' + o.id + '"><span class="glyphicon glyphicon-tasks"></span>&nbsp;&nbsp;Details</a></li>' +
								'</ul>' +
							'</div>' +
						'</td>' +
					'</tr>';
					if (k == data.objects.length - 1) {
						next();
					}
				});
			});
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
			/*
			var timer = function () {
				if (rows.length == data.objects.length && (rows.length == 0 || rows[0] != '')) {
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
				} else {
					window.setTimeout(timer, 100);
				}
			};
			timer();*/
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
		'<div class="modal-dialog modal-sm">' +
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

CalculationsManager.prototype.loadDetail = function (url, id) {
	var self = this;
	
	$.getJSON(url, function (data) {
		
		$.getJSON(data.user, function (subdata) {
			var loader = $('#' + self.module + '-detail-' + id + ' ~ .dots');
			var ajaxLoaded = 0;
			var mtime = new Date();
			mtime.setISO8601(data.mtime);
			var rows = [
				'<div class="ajax-hide">',
				'<ul class="media-list">',
				'<li class="media"><strong class="pull-left">User</strong><div class="media-body">' + subdata.username + '</div></li>',
				'<li class="media"><strong class="pull-left">Description</strong><div class="media-body">' + data.description + '</div></li>',
				'<li class="media"><strong class="pull-left">Type</strong><div class="media-body">' + data.type + '</div></li>',
				'<li class="media"><strong class="pull-left">Attributes</strong><div class="media-body"><ul class="media-list">'
			];
		
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
		
			$.each(data.attributes, function (k, v) {
				if (v instanceof Array) {
					v = v.join('<br>');
				} else if (typeof v === 'number') {
					v = String(v);
				} else if (typeof v === 'object') {
					var content = ['<dl class="dl-horizontal">'];
					$.each(v, function (key, val) {
						content.push('<dt>' + key.trunc(18, false, true) + '</dt>');
						content.push('<dd>' + val + '</dd>');
					});
					content.push('</dl>');
					v = content.join('');
				} else if (k === 'scheduler_lastchecktime') {
					var time = new Date();
					time.setISO8601(v);
					v = time.toLocaleString();
				} else if (k === 'state') {
					v = self.colorState(v);
				} else if (k === 'scheduler_state') {
					v = self.colorSchedulerState(v);
				} else {
					v = v.trunc(100);
				}
				rows.push('<li class="media"><strong class="pull-left">' + k.trunc(18, false, true) +
					'</strong><div class="media-body">' + v + '</div></li>');
			});
			
			/*$.each(data.attributes, function (k, v) {
				var rowstart = rows.length;
				rows.push(''); // reserve a spot
				// here do the ajax to get attribute infos, and then update the corresponding row
				$.getJSON(v, function (subdata) {
					if (subdata.value instanceof Array) {
						subdata.value = subdata.value.join('<br>');
					} else if (typeof subdata.value === 'number') {
						subdata.value = String(subdata.value);
					} else if (typeof subdata.value === 'object') {
						var content = ['<dl class="dl-horizontal">'];
						$.each(subdata.value, function (key, val) {
							content.push('<dt>' + key.trunc(18, false, true) + '</dt>');
							content.push('<dd>' + val + '</dd>');
						});
						content.push('</dl>');
						subdata.value = content.join('');
					} else if (subdata.key === 'scheduler_lastchecktime') {
						var time = new Date();
						time.setISO8601(subdata.value);
						subdata.value = time.toLocaleString();
					} else if (subdata.key === 'state') {
						subdata.value = self.colorState(subdata.value);
					} else if (subdata.key === 'scheduler_state') {
						subdata.value = self.colorSchedulerState(subdata.value);
					} else {
						subdata.value = subdata.value.trunc(100);
					}
					rows[rowstart] = '<li class="media"><strong class="pull-left">' + subdata.key.trunc(18, false, true) +
						'</strong><div class="media-body">' + subdata.value + '</div></li>';
					ajaxLoaded++;
					if (ajaxLoaded == data.attributes.length + data.inputs.length + data.outputs.length) {
						next();
					}
				});
			});*/
			rows.push(
				'</ul></div></li>',
				'<li class="media"><strong class="pull-left">Inputs</strong><div class="media-body"><dl class="dl-horizontal">'
			);
			// instead of querying each url, there is an endpoint dbnode/id/inputs which shows the basic necessary informations
			// query this endpoint instead and go through the list
			$.each(data.inputs, function (k, v) { /* we go over all inputs and display them in a nested way */
				var rowstart = rows.length; // index of the input row
				rows.push(''); // reserve a spot
				$.getJSON(v, function (subdata) {
					rows[rowstart] = '<dt style="width: 30px;">' + subdata.id + '</dt><dd style="margin-left: 50px;"><a href="' +
					self.getUrl('apidetail') + subdata.id + '/' +
					'" target="_blank" class="text-info"><span class="glyphicon glyphicon-new-window"></span></a>&nbsp;&nbsp;<a href="#">' +
						subdata.type + '</a></dd>';
					ajaxLoaded++;
					if (ajaxLoaded == data.inputs.length + data.outputs.length) {
						next();
					}
				});
			});
			rows.push(
				'</dl></div></li>',
				'<li class="media"><strong class="pull-left">Outputs</strong><div class="media-body"><dl class="dl-horizontal">'
			);
			// instead of querying each url, there is an endpoint dbnode/id/outputs which shows the basic necessary informations
			// query this endpoint instead and go through the list
			$.each(data.outputs, function (k, v) { /* we go over all outputs and display them in a nested way */
				var rowstart = rows.length; // index of the output row
				rows.push(''); // reserve a spot
				$.getJSON(v, function (subdata) {
					rows[rowstart] = '<dt style="width: 30px;">' + subdata.id + '</dt><dd style="margin-left: 50px;"><a href="' +
					self.getUrl('apidetail') + subdata.id + '/' +
					'" target="_blank" class="text-info"><span class="glyphicon glyphicon-new-window"></span></a>&nbsp;&nbsp;<a href="#">' +
						subdata.type + '</a></dd>';
					ajaxLoaded++;
					if (ajaxLoaded == data.inputs.length + data.outputs.length) {
						next();
					}
				});
			});
			rows.push(
				'</dl></div></li>',
				'<li class="media"><strong class="pull-left">Modification</strong><div class="media-body">' + mtime.toLocaleString() + '</div></li>',
				'<li class="media"><strong class="pull-left">Node version</strong><div class="media-body">' + data.nodeversion + '</div></li>',
				'<li class="media"><strong class="pull-left">UUID</strong><div class="media-body">' + data.uuid + '</div></li>',
				'</ul></div>'
			);
		});
	});
};

// get ajax url for a function
CalculationsManager.prototype.getUrl = function (action) {
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
CalculationsManager.prototype.getAPIUrl = function (resource) {
	var url = api_urls[resource];
	if (url.slice(-2) == '/0') {
		return url.substring(0, url.length - 1);
	} else if (url.slice(-3) == '/0/') {
		return url.substring(0, url.length - 2);
	} else {
		return url;
	}
};

// get colored state, warning is orange, info is light blue, danger is red, success is green, primary is blue, default is grey
CalculationsManager.prototype.colorState = function (state) {
	var states = {
		'NEW'				: 'warning',
		'TOSUBMIT'			: 'info',
		'SUBMITTING'		: 'default',
		'COMPUTED'			: 'default',
		'RETRIEVING'		: 'default',
		'PARSING'			: 'default',
		'WITHSCHED'			: 'primary',
		'FINISHED'			: 'success',
		'SUBMISSIONFAILED'	: 'danger',
		'RETRIEVALFAILED'	: 'danger',
		'PARSINGFAILED'		: 'danger',
		'FAILED'			: 'danger'
	};
	if (states[state] !== undefined) {
		return '<span class="label label-' + states[state] + '">' + state + '</span>';
	} else {
		return state;
	}
};

// get colored state, warning is orange, info is light blue, danger is red, success is green, primary is blue, default is grey
CalculationsManager.prototype.colorSchedulerState = function (state) {
	var states = {
		'QUEUED'			: 'info',
		'QUEUED_HELD'		: 'warning',
		'RUNNING'			: 'primary',
		'SUSPENDED'			: 'warning',
		'DONE'				: 'success'
	};
	if (states[state] !== undefined) {
		return '<span class="label label-' + states[state] + '">' + state + '</span>';
	} else {
		return state;
	}
};

// add an error message to the page DOM
CalculationsManager.prototype.errorMessage = function (action, id, error) {
	var message = {
		disable: 'Could not disable computer ' + id,
		enable: 'Could not enable computer ' + id
	}
	$('body>div.container').prepend('<div class="alert alert-danger"><strong>Oops</strong>, there was a problem.' +
		message[action] + ' : ' + error + '</div>');
};

// add an error message to the modal box
CalculationsManager.prototype.errorModal = function (field, error) {
	this.modal.find('.alert').html('<strong>Oops</strong>, there was a problem : ' + error)
		.show();
	field.parent().addClass('has-error');
	field.select().focus();
};

