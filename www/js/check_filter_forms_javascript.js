
function checkFilterFormsJavascriptLoaded() {
	if (typeof(allFieldsDict) == 'undefined') {
		var elems = Ext.query('.for_fields_button');
		for (var i = 0; i < elems.length; i++) {
			var elem = elems[i];
			var err = document.createElement('p');
			err.appendChild(document.createTextNode('Error loading data for filter button!'));
			err.className = 'error';
			elem.appendChild(err);
		}
	}
}

Ext.onReady(checkFilterFormsJavascriptLoaded);