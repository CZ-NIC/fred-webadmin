
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

/* Generate choices for ActionType filter field in log request filter form. */
function filter_action_types() {
    var action_select = document.getElementById("logger_action_type_id");
    if (action_select == null) {
        /* ActionType field is not active => do nothing. */
        return;
    }
    var service_select = document.getElementById("logger_service_type_id");
    var actions = []
    var show_all = service_select == null || service_select.selectedIndex == 0
    if (show_all) {
        /* Glue together all the choices for every service type and display
         * them all. */
        var actions_by_types = get_actions();
        for (a in actions_by_types) {
            actions = actions.concat(actions_by_types[a])
        }
    } else {
        /* Only display the actions for the given service type. */
        // Minus one for the empty type.
        var index = service_select.selectedIndex - 1;
        var actions_by_types = get_actions();
        actions = actions_by_types[index]
    }
    /* Delete all the choices except the empty value. */
    action_select.length = 1;

    /* Display the action choices. */
    for (var i=0; i<actions.length; ++i) {
        var newOption = document.createElement('option');
        action_select.add(newOption, null);
        newOption.value = actions[i][0];
        newOption.innerHTML = actions[i][1];
        newOption.innerText = actions[i][1];
    }
}

Ext.onReady(checkFilterFormsJavascriptLoaded);
