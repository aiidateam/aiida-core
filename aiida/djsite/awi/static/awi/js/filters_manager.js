function FiltersManager(module, moduleManager) {
	this.moduleManager = moduleManager;
	this.module = module;
	this.panel = $('#filters');
	this.newDropdown = $('#filters-new');
	this.modalId = 'filter-modal';
	this.modal = $('#' + this.modalId);
	this.operators = {
		'boolean': {
			exact: 	['=', 'exactly']
		},
		integer: {
			exact: 	['=', 'equal'],
			gt: 	['>', 'greater than'],
			lt: 	['<', 'lower than'],
			gte: 	['>=', 'greater or equal'],
			lte: 	['<=', 'lower or equal'],
			range: 	['<>', 'in range']
		},
		string: {
			icontains: 		['~', 'contains'],
			istartswith: 	['^', 'starts with'],
			iendswith: 		['$', 'ends with'],
			iexact: 		['=', 'exactly'],
			isnull: 		['0', 'is null']
		},
		list: {
			exact: ['=', 'exactly']
		},
		datetime: {
			gte: 	['>=', 'after'],
			lte: 	['<=', 'before'],
			range: 	['<>', 'in range'],
			year: 	['y', 'year']
		}
	};
	
	this.listen();
	this.load();
}

// listen for click events on buttons and links
FiltersManager.prototype.listen = function () {
	var self = this;
	
	// remove filter
	this.panel.delegate('button.filter-remove', 'click', function (e) {
		e.preventDefault();
		var field = $(this).attr('data-field');
		self.remove(field);
	});
	
	// change operator in dropdown
	this.panel.delegate('a.filter-change-operator', 'click', function (e) {
		e.preventDefault();
		var field = $(this).attr('data-field');
		var operator = $(this).attr('data-operator');
		self.changeOperator(field, operator);
	});
	
	// open modal box for value change
	this.panel.delegate('a.filter-change-value', 'click', function (e) {
		e.preventDefault();
		var field = $(this).attr('data-field');
		var value = $(this).text();
		self.openValueModal(field, value);
	});
	
	// the modal size needs to change depending on the displayed content :
	// small for value changes but
	// normal for creating new filters
	this.newDropdown.delegate('a', 'click', function () {
		self.modal = self.modal.refresh();
		self.modal.find('.modal-dialog').removeClass('modal-sm');
	});
	this.newDropdown.delegate('button.filter-value', 'click', function () {
		self.modal = self.modal.refresh();
		self.modal.find('.modal-dialog').addClass('modal-sm');
	});
};

// remove filter
FiltersManager.prototype.remove = function (field) {
	var self = this;
	
	$.ajax({
		url: self.getUrl('remove') + field,
		type: 'GET',
		success: function (data) {
			self.load();
			// false to not scroll to beginning of the table after reload
			self.moduleManager.load(false);
			//window['load_'+module](false, $('#'+module+'-list').attr('data-ordering'));
		},
		error: function (xhr, status, error) {
			self.errorMessage('remove', field, xhr.responseText);
		}
	});
};

// change operator on a field filter
FiltersManager.prototype.changeOperator = function (field, operator) {
	var self = this;
	
	$.ajax({
		url: self.getUrl('set') + field,
		type: 'POST',
		data: {
			'operator': operator
		},
		success: function (data) {
			self.load();
			// false to not scroll to beginning of the table after reload
			self.moduleManager.load(false);
			//window['load_'+module](false, $('#' + module + '-list').attr('data-ordering'));
		},
		error: function (xhr, status, error) {
			self.errorMessage('operator', field, xhr.responseText);
		}
	});
};

// open modal for value change
FiltersManager.prototype.openValueModal = function (field, value) {
	var self = this;
	
	$.ajax({
		url: self.getUrl('set') + field,
		type: 'POST',
		data: {
			'value': value
		},
		success: function (data) {
			self.load();
			// false to not scroll to beginning of the table after reload
			self.moduleManager.load(false);
			//window['load_' + module](false, $('#' + module + '-list').attr('data-ordering'));
		},
		error: function (xhr, status, error) {
			self.errorMessage('value', field, xhr.responseText);
		}
	});
};

// load the filters
FiltersManager.prototype.load = function () {
	var self = this;
	
	//if there was already content in filters panel, remove it and show the loader
	this.panel.children('div.btn-group').remove();
	this.panel.children('.loader').fadeIn('fast');
	
	$.get(this.getUrl('get'), function (data) {
		self.panel.children('.loader').fadeOut('fast', function () {
			self.panel.prepend(data);
			// load options for the new filter dropdown directly from API, disable links if filter already set
			self.newDropdown.html('');
			$.getJSON(self.getUrl('schema'), function (data) {
				$.each(data.filtering, function (k, o) {
					// we check if there is already a filter for this field
					if (self.panel.find('#filter-' + k).length == 0) {
						self.newDropdown.append('<li><a href="' +
							self.getUrl('create') +	k +
							'" data-toggle="modal" data-target="#filter-modal">' +
							data.fields[k].display_name + '</a></li>');
					} else {
						self.newDropdown.append('<li class="disabled"><a href="#">' +
							data.fields[k].display_name + '</a></li>');
					}
				});
			});
		});
	});
};

// load filters markup
FiltersManager.prototype.loadFilters = function (filters) {
	var self = this;
	
	// display the operator choices for each filter
	console.log(filters.toString());
	$.each(filters, function (k, f) {
		var o = self.operators[f.type];
		$('#filter-' + f.field + ' button.filter-operator').text(o[f.operator][0]);
		if (f.type != 'list' && f.type != 'boolean') {
			$('#filter-' + f.field + ' ul.filter-operators').html(function () {
				var content = [];
				for (var op in o) {
					if (o.hasOwnProperty(op)) {
						content.push('<li><a href="#" data-operator="' + op + '" data-field="' + f.field + '" class="filter-change-operator"><strong>' +
							o[op][0] + '</strong>&nbsp;&nbsp;&nbsp;' + o[op][1] + '</a></li>');
					}
				}
				return content.join('');
			});
		}
	});
	// ajax to get the possible values for "list" type filters (direct API call)
	$.getJSON(this.getUrl('schema'), function (data) {
		$.each(data.fields, function (k, o) {
			if ($('#filter-' + k + ' .filter-list').length > 0) {
				$('#filter-' + k + ' ul.filter-values').html(function () {
					var content = [];
					if (o.type == 'boolean') {
						content.push('<li><a href="#" data-field="' + k + '" class="filter-change-value text-success">true</a></li>');
						content.push('<li><a href="#" data-field="' + k + '" class="filter-change-value text-danger">false</a></li>');
					}
					else {
						for (var v in o.valid_choices) {
							if (o.valid_choices.hasOwnProperty(v)) {
								content.push('<li><a href="#" data-field="' + k + '" class="filter-change-value">' + v + '</a></li>');
							}
						}
					}
					return content.join('');
				});
			}
		});
	});
	// we add the required modal for filters needs somewhere in the body where it isn't affected by css
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

FiltersManager.prototype.loadValue = function (fieldname, type, operator) {
	var self = this;
	this.modal = this.modal.refresh();
	
	this.modal.find('h4').append(' <small>' + self.operators[type][operator][1] + '</small>');
	
	var field = this.modal.find('input.form-control');
	var fieldval = $('#filter-' + fieldname + ' button.filter-value').text();
	// for the is_null operator, we replaced the content by a non-breaking space, which we need to rule out here
	if (fieldval != '\xA0')
		field.val(fieldval);
	window.setTimeout(function () {
		field.select().focus();
	}, 500);
	this.modal.find('button.btn').click(function () {
		$.ajax({
			url: self.getUrl('set') + fieldname,
			type: 'POST',
			data: {'value': field.val()},
			success: function (data) {
				// reload the filters and reload the list
				self.modal.modal('toggle');
				self.load();
				self.moduleManager.load(false);
			},
			error: function (xhr, status, error) {
				self.errorModal(field, xhr.responseText);
			}
		});
	});
	// on pressing the enter key, trigger the click event on the button (submit)
	field.keypress(function (event) {
		if (event.which == 13) {
			self.modal.find('button.btn').click();
		}
	});
	// after apparition animation is complete, focus on the field
	this.modal.on('shown.bs.modal', function (e) {
		field.select().focus();
	});
	// if there was an error message, hide it on modal apparition
	this.modal.on('show.bs.modal', function (e) {
		field.parent().removeClass('has-error');
		self.modal.find('.alert').hide();
	});
};

FiltersManager.prototype.loadCreate = function (fieldname, type) {
	var self = this;
	this.modal = this.modal.refresh();
	
	var o = this.operators[type];
	if (type != 'list') {
		this.modal.find('select#filter-operator').html(function () {
			var content = [];
			for (var op in o) {
				if (o.hasOwnProperty(op)) {
					content.push('<option value="' + op + '">' + o[op][0] + '&nbsp;&nbsp;&nbsp;' + o[op][1] + '</option>');
				}
			}
			return content.join('');
		});
	} else {	
		$.getJSON(self.getUrl('schema'), function (data) {
			self.modal.find('select#filter-value').html(function () {
				var content = [];
				for (var v in data.fields[fieldname].valid_choices) {
					content.push('<option value="' + v + '">' + v + '</option>');
				}
				return content.join('');
			});
		});
	}
	if (type == 'boolean') {
		this.modal.find('button.filter-bool').click(function () {
			var value_bool = $(this).attr('data-value');
			$.ajax({
				url: self.getUrl('set') + fieldname,
				type: 'POST',
				data: {
					'operator': 'exact',
					'value': value_bool
				},
				success: function (data) { /* if everything ok */
					// reload the filters and reload the list
					self.modal.modal('toggle');
					self.load();
					self.moduleManager.load(false);
				},
				error: function (xhr, status, error) {
					self.errorModal(null, xhr.responseText);
				}
			});
		});
	}
	
	if (type != 'list' && type != 'boolean') {
		var operator_field = this.modal.find('select#filter-operator');
		if (type != 'datetime') {
			var value_field = this.modal.find('input#filter-value');
			value_field.val($('#filter-' + fieldname + ' button.filter-value').text());
			window.setTimeout(function () {
				// we focus on the input field when the animation is over (just required for the first load, is then handled by the event show.bs.modal)
				value_field.select().focus();
			}, 1000);
		}
	}
	
	if (type == 'datetime') {
		operator_field.change(function () {
			var option = $(this).children('option:selected').val();
			if (option == 'range') {
				self.modal.find('.filter-datetime').hide();
				self.modal.find('#filter-datetime-range').show();
			} else if (option == 'year') {
				self.modal.find('.filter-datetime').hide();
				self.modal.find('#filter-datetime-year').show();
			} else {
				self.modal.find('.filter-datetime').hide();
				self.modal.find('#filter-datetime-single').show();
			}
		});
	} else if (type == 'integer') {
		operator_field.change(function () {
			var option = $(this).children('option:selected').val();
			if (option == 'range') {
				self.modal.find('.filter-integer').hide();
				self.modal.find('#filter-integer-range').show();
				self.modal.find('#filter-integer-range #filter-value-low').focus();
			} else {
				self.modal.find('.filter-integer').hide();
				self.modal.find('#filter-integer-single').show();
			}
		});
	}
	
	if (type != 'boolean') {
		this.modal.find('button.filter-submit').click(function () {
			if (type != 'list' && type != 'boolean' && type != 'datetime' && type != 'integer') {
				var post_operator = operator_field.children('option:selected').val();
				var post_value = value_field.val();
			} else if (type == 'integer') {
				var post_operator = operator_field.children('option:selected').val();
				var option = operator_field.children('option:selected').val();
				if (option == 'range') {
					var post_value = self.modal.find('#filter-value-low').val() + ';' + self.modal.find('#filter-value-high').val();
				} else {
					var post_value = value_field.val();
				}
			} else if (type == 'datetime') {
				var post_operator = operator_field.children('option:selected').val();
				var option = operator_field.children('option:selected').val();
				if (option == 'range') {
					var post_value = self.modal.find('#filter-datetime-start').val() + 'T00:00;' + self.modal.find('#filter-datetime-end').val() + 'T23:59:59';
				} else if (option == 'year') {
					var post_value = self.modal.find('#filter-datetime-year').val();
				} else if (option == 'gte') {
					var post_value = self.modal.find('#filter-value').val() + 'T00:00';
				} else if (option == 'lte') {
					var post_value = self.modal.find('#filter-value').val() + 'T23:59:59';
				} else {
					var post_value = '';
				}
			} else if (type == 'list') {
				var post_operator = 'exact';
				var post_value = self.modal.find('select#filter-value option:selected').val();
			}
			$.ajax({
				url: self.getUrl('set') + fieldname,
				type: 'POST',
				data: {
					'operator': post_operator,
					'value': post_value
				},
				success: function (data) {
					// reload the filters and reload the list
					self.modal.modal('toggle');
					self.load();
					self.moduleManager.load(false);
				},
				error: function (xhr, status, error) {
					if (type == 'list' || type == 'boolean') {
						self.errorModal(null, xhr.responseText);
					} else {
						self.errorModal(value_field, xhr.responseText);
					}
				}
			});
		});
	}
	
	if (type != 'list' && type != 'boolean') {
		// on pressing the enter key, trigger the click event on the button (submit)
		value_field.keypress(function (event) {
			if (event.which == 13) {
				self.modal.find('button.btn').click();
			}
		});
	}
	if (type != 'list' && type != 'boolean' && type != 'datetime') {
		// after apparition animation is complete, focus on the field
		self.modal.on('shown.bs.modal', function (e) {
			value_field.select().focus();
		});
	}
	// if there was an error message, hide it on modal apparition
	self.modal.on('show.bs.modal', function (e) {
		if (type != 'list' && type != 'boolean' && type != 'datetime') {
			value_field.parent().removeClass('has-error');
		}
		self.modal.find('.alert').hide();
	});
};

// get ajax url for a function, without the field parameter at the end
FiltersManager.prototype.getUrl = function (action) {
	var url = modules_urls.filters[this.module][action];
	if (url.slice(-2) == '/0') {
		return url.substring(0, url.length - 1);
	} else {
		return url;
	}
};

// add an error message to the page DOM
FiltersManager.prototype.errorMessage = function (action, field, error) {
	var message = {
		remove: 'Could not remove filter on field ' + field,
		operator: 'Could not change operator on filter for field ' + field,
		value: 'Could not change value on filter for field ' + field
	}
	$('body>div.container').prepend('<div class="alert alert-danger"><strong>Oops</strong>, there was a problem.' +
		message[action] + ' : ' + error + '</div>');
};

// add an error message to the modal box
FiltersManager.prototype.errorModal = function (field, error) {
	this.modal.find('.alert').html('<strong>Oops</strong>, there was a problem : ' + error)
		.show();
	if (field !== null) {
		field.parent().addClass('has-error');
		field.select().focus();
	}
};

