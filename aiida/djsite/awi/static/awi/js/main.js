/**
* main2.js
* Scripts used in AiiDA Web Interface (AWI), common to all pages
* http://www.aiida.net
*/
/* We first make sure jQuery is loaded */
if (!jQuery) { throw new Error("AiiDA Web Interface requires jQuery") }

/* custom function to truncate a string after so many characters, optionally after a word, and append an ellipsis */
String.prototype.trunc = function (n,useWordBoundary) {
	var toLong = this.length>n,
	s_ = toLong ? this.substr(0,n-1) : this;
	s_ = useWordBoundary && toLong ? s_.substr(0,s_.lastIndexOf(' ')) : s_;
	return  toLong ? s_ + '&hellip;' : s_;
};

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