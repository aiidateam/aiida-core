/**
* main2.js
* Scripts used in AiiDA Web Interface (AWI), common to all pages
* http://www.aiida.net
*/
/* We first make sure jQuery is loaded */
if (!jQuery) { throw new Error("AiiDA Web Interface requires jQuery") }

/* custom function to truncate a string after so many characters, optionally after a word, and append an ellipsis */
String.prototype.trunc = function (n,useWordBoundary,tooltip) {
	var tooLong = this.length>n,
	s_ = tooLong ? this.substr(0,n-1) : this;
	s_ = useWordBoundary && tooLong ? s_.substr(0,s_.lastIndexOf(' ')) : s_;
	if (tooLong) {
		if (tooltip) {
			return '<span title="' + this + '" data-toggle="tooltip">' + s_ + '&hellip;</span>';
		} else {
			return s_ + '&hellip;';
		}
	} else {
		return s_;
	}
};

/* parse iso-8601 date format if not supported */
Date.prototype.setISO8601 = function (string) {
	var regexp = "([0-9]{4})(-([0-9]{2})(-([0-9]{2})" +
		"(T([0-9]{2}):([0-9]{2})(:([0-9]{2})(\.([0-9]+))?)?" +
		"(Z|(([-+])([0-9]{2}):([0-9]{2})))?)?)?)?";
	var d = string.match(new RegExp(regexp));

	var offset = 0;
	var date = new Date(d[1], 0, 1);

	if (d[3]) { date.setMonth(d[3] - 1); }
	if (d[5]) { date.setDate(d[5]); }
	if (d[7]) { date.setHours(d[7]); }
	if (d[8]) { date.setMinutes(d[8]); }
	if (d[10]) { date.setSeconds(d[10]); }
	if (d[12]) { date.setMilliseconds(Number("0." + d[12]) * 1000); }
	if (d[14]) {
		offset = (Number(d[16]) * 60) + Number(d[17]);
		offset *= ((d[15] == '-') ? 1 : -1);
	}

	offset -= date.getTimezoneOffset();
	time = (Number(date) + (offset * 60 * 1000));
	this.setTime(Number(time));
}

/* little helper */
function nl2br(str, is_xhtml) {
	var breakTag = (is_xhtml || typeof is_xhtml === 'undefined') ? '<br />' : '<br>';
	return (str + '').replace(/([^>\r\n]?)(\r\n|\n\r|\r|\n)/g, '$1' + breakTag + '$2');
}

$(document).ready(function () {
	$.fn.refresh = function() {
		return $(this.selector);
	};
});