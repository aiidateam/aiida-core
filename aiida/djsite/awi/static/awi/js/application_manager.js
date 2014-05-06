function ApplicationManager(module, FiltersManager, ModuleManager) {
	this.module = module;
	this.moduleManager = new ModuleManager(this);
	this.filtersManager = new FiltersManager(this.module, this.moduleManager);
	
	this.listen();
}

// listen for click events on buttons and links
ApplicationManager.prototype.listen = function () {
	var self = this;
	
	this.moduleManager.pagination.delegate('a', 'click', function (e) {
		e.preventDefault();
		var me = $(this);
		if (me.parent().hasClass('disabled')) {
			return false;
		} else {
			self.moduleManager.loadUrl = me.attr('data-url');
			// load the new list with this new API url, true to scroll to the beginning of the table after loading
			self.moduleManager.load(true);
		}
	});
};

// generate the pagination markup
ApplicationManager.prototype.pagination = function (total, limit, offset, previous, next) {
	var output = [];
	if (previous != null)
		output.push('<li><a href="#" data-url="' + previous + '">&laquo;</a></li>');
	else
		output.push('<li class="disabled"><a href="#">&laquo;</a></li>');
	for (var i = 1; i <= Math.ceil(total / limit); i++) {
		if (offset == (i - 1) * limit)
			var aclass = ' class = "active"';
		else
			var aclass = '';
		// append the selection criteria, but only if they aren't already present, also check if the order_by is already present
		var firstChar;
		if (this.moduleManager.loadUrl.indexOf('?') == -1)
			firstChar = '?';
		else
			firstChar = '&';
		
		var append;
		if (this.moduleManager.loadUrl.indexOf('limit') === -1) {
			append = firstChar + 'limit=' + limit + '&offset=' + ((i - 1) * limit);
		} else if (this.moduleManager.loadUrl.indexOf('offset') !== -1) {
			this.moduleManager.loadUrl = this.moduleManager.loadUrl.replace(/&offset=\d+/g, '');
			append = firstChar + 'offset=' + ((i - 1) * limit);
		} else if (this.moduleManager.loadUrl.indexOf('limit') !== -1) {
			append = firstChar + 'offset=' + ((i - 1) * limit);
		} else {
			append = '';
		}
		
		output.push('<li' + aclass + '><a href="#" data-url="' + this.moduleManager.loadUrl + append + '">' + i + '</a></li>');
	}
	if (next != null)
		output.push('<li><a href="#" data-url="' + next + '">&raquo;</a></li>');
	else
		output.push('<li class="disabled"><a href="#">&raquo;</a></li>');
	return output.join("");
};
