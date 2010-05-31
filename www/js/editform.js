
function setCleanOrDirty(field, defaultValue, newValue) {
    if ((field.type == 'hidden') || (field.type == 'submit')) 
        return;
    if (newValue == defaultValue) {
        Ext.get(field).parent('tr').dom.style.backgroundColor='white';
    } else {
        Ext.get(field).parent('tr').dom.style.backgroundColor='#FCC';
    }
    /*if (field.type == 'checkbox' || field.type == 'radiobox') {
        if (newValue == defaultValue) {
            field.style.color = 'black';
        } else {
            field.style.color = 'red';
        }       
    } else {
	    if (newValue == defaultValue) {
	        field.style.backgroundColor = 'white';
	    } else {
	        field.style.backgroundColor = 'red';
	    }
    }*/
}

function fieldOnChange(event) {
    log('fieldOnChange');
    var field;
    if (event.target) {
        field = event.target;
    } else {
        field = event;
    }

    if (field.type == 'checkbox' || field.type == 'radiobox') {
        setCleanOrDirty(field, field.title, field.checked?'checked':'unchecked');
    } else {
        setCleanOrDirty(field, field.title, field.value);
    }
}

function fieldOnKeyPress(event) {
    log('zmacktnuto');
    var field = event.target;
    delayedTask = new Ext.util.DelayedTask(fieldOnChange, this, [field]);
    delayedTask.delay(50);
}

function fieldOnClick(event) {
    log('clicckedd');
    var field = event.target;
    // call onchange event to field:
    if (field.fireEvent) { // IE
        field.fireEvent('onChange');
    } else { // GECKO
        var evt = document.createEvent('HTMLEvents');
        evt.initEvent('change', false, false);
        field.dispatchEvent(evt);
    }
}

function setSpecialBehaviourToFields() {
    Ext.select('.editform_table').each(function (form) {
	    log('form: ', form);
	    log('fields:', form.select('input'));
        // "select:not([multiple])"
	    form.select('input, select').each(function (field) {
	        log('Pridavam onchange to field', field);
            // field.set({'title': field.dom.value}); tohle musi delat server, pac ty data se mohli zmenit pokud je chyba ve formulari a formular je zobrazen znova
	        field.on('change', fieldOnChange);
            field.on('keypress', fieldOnKeyPress);
            field.on('blur', fieldOnChange); // this line is here because firefox bug - onchange is not called when using form history, si it is called here manually
            field.on('click', fieldOnClick); // this is here for the same reason as line above (but it is propably not helping so much :))
            fieldOnChange(field.dom);
	    });
    });
}

/** Disables registrar handle field when associating a Payment with 
 *  a different type than "to/from registrar". **/
function disableRegistrarHandle() {
    registrar_handle_input_array = document.getElementsByName("handle");
    registrar_handle_input = registrar_handle_input_array[0];
    type_array = document.getElementsByName("type");
    type = type_array[0];
    if (type.selectedIndex == 0)
        registrar_handle_input.disabled = false;
    else
        registrar_handle_input.disabled = true;
}

function show_hide(element_id, button_id, skip_effect) {
    use_effect = typeof(skip_effect) == 'undefined' ? true : !skip_effect;
    var field_elem = document.getElementById(element_id)
    var btn_elem = document.getElementById(button_id)

    if (field_elem.style.display == "none") {
        if (use_effect)
            slideDown(field_elem, {duration: 0.45});
        else
            field_elem.style.display = "block";
        btn_elem.innerText = "hide";
    } else {
        if (use_effect)
            slideUp(field_elem, {duration: 0.45});
        else
            field_elem.style.display = "none";
        btn_elem.innerText = "show";
    }
}


connect(window, 'onload', onload_hide_registrar_editform_fields); 
function onload_hide_registrar_editform_fields(e) {
    show_hide("authentications_id", "authentications_id_display", true);
    show_hide("zones_id", "zones_id_display", true);
    show_hide("groups_id", "groups_id_display",  true);
    show_hide("certifications_id", "certifications_id_display", true);
}

Ext.onReady(setSpecialBehaviourToFields);
