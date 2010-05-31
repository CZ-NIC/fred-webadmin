
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

function filter_action_types() {
    var action_select = document.getElementById("logger_action_type_id");
    if (action_select == null) {
        return;
    }
    var service_select = document.getElementById("logger_service_type_id");
    var actions;
    var show_all = service_select == null || service_select.selectedIndex == 0
    if (show_all) {
        actions = get_actions()[0];
    } else {
        var index = service_select.selectedIndex - 1; // Minus one for the empty type.
        var actions_by_types = get_actions();
        actions = actions_by_types[index]
    }
    action_select.length = 1;
    if (typeof(actions) == "undefined") {
        return;
    }
    for (var i=0; i<actions.length; ++i) {
        var newOption = document.createElement('option');
        action_select.add(newOption)
        newOption.value = actions[i][0];
        newOption.innerHTML = actions[i][1];
        newOption.innerText = actions[i][1];
    }
}

Ext.onReady(checkFilterFormsJavascriptLoaded);
