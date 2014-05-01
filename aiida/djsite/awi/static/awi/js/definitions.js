/**
* definitions.js
* Base definitions of hard-coded stuff
* http://www.aiida.net
*/

/* we need to be able to access those objects from external scripts */
var filters_operators = {
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

