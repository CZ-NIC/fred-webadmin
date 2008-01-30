
function formContentToObject(formContent) {
	obj = {};
	keys = formContent[0];
	vals = formContent[1];
	for (var i = 0; i < keys.length; i++) {
		var key = keys[i];
		var val = vals[i];
		if (isUndefined(obj[key])) {
			obj[key] = val;
		} else { // for example multi-select have more values under same key, so we'll create array and pushing values to it
			prev_val = obj[key];
			if (!(prev_val instanceof Array))
				obj[key] = [prev_val]
			obj[key].push(val)
		}
	}
	return obj;
}

function delRow(thisElem, fieldName, fieldLabel) {
	var tr = getFirstParentByTagAndClassName(thisElem, 'tr');
	
	// add field back to field chooser and make field chooser visible
	var select = findChildElements(tr.parentNode, ['> tr.and_row > td > select'])[0];
	select.options[select.options.length]=new Option(fieldLabel, fieldName);
	var fieldChooserTr = getFirstParentByTagAndClassName(select, tagName='tr');
	fieldChooserTr.style.visibility = 'visible';
	
	// and finally remove field
	tr.parentNode.removeChild(tr);
}

function getNameToAdd(tr) {
	// get name of field, which will be added in addRow*
	var fieldChooser = getFirstElementByTagAndClassName('select', '', tr);
	return fieldChooser.value
}

function addOrForm(thisElem) {
	var my_tr = getFirstParentByTagAndClassName(thisElem, tagName='tr');
	var or_tr = TR({'class': 'or_row'});
	var form_tr = TR();
	insertSiblingNodesBefore(my_tr, or_tr);
	insertSiblingNodesBefore(my_tr, form_tr);
	or_tr.innerHTML = buildOrRow();
	form_tr.innerHTML = buildForm();
}



function getFieldRowData(fieldRow) {
	var rowData = {};

	var innerFTable = findChildElements(fieldRow, ['.filtertable'])[0];
	if (innerFTable) { //compound field
		var td = getFirstElementByTagAndClassName('td', '', fieldRow);
		
		// presention (with velue as position) aned negation inputs:
		var presAndNegInputs = findChildElements(fieldRow, ['> td > input']);
		rowData[presAndNegInputs[0].name] = presAndNegInputs[0].value;
		if (presAndNegInputs[1].checked)
			rowData[presAndNegInputs[1].name] = presAndNegInputs[1].value;
		
		// inner filtertable:
		var negInput = presAndNegInputs[1];
		var filterName = negInput.name.replace('negation', 'filter');
		log('fn, nn:' + filterName + ', ' + negInput.name);
		var innerTableData = {};
		innerTableData[filterName] = getFTableData(innerFTable);
		update(rowData, innerTableData);
	} else {
		rowData = formContentToObject(formContents(fieldRow));
	}
	log('j_rowData = ' + serializeJSON(rowData));
	return rowData;
}

function getFTableData(ftable) {
	var ftData = {}; // {} is same as (now deprecated): new Object();
	var fieldRows = findChildElements(ftable, ['> tbody > tr.field_row']);
	log('fieldRows.length = ' + fieldRows.length);
	for (var i = 0; i < fieldRows.length; i++) {
		var fieldRow = fieldRows[i];
		update(ftData, getFieldRowData(fieldRow));
	}
	//update(ft_data, {'ahoj': 'cau'})
	return ftData
}

function sendUnionForm(thisElem) {
	var data = [];
	
	var ftables = $$('.unionfiltertable > tbody > tr > td > .filtertable');
	log('ftables = ' + ftables);
	
	for (var i = 0; i < ftables.length; i++) {
		var ftable = ftables[i];
		log('row ' + ftable);
		data.push(getFTableData(ftable));
	}
	
	log('data = ' + data);
	log('json_data = ' + serializeJSON(data));
	//var form = FORM({'method':'post'}, INPUT({'type': 'hidden', 'name': 'data', 'value': encodeURIComponent(serializeJSON(data))}));
	var form = FORM({'method':'post', 'action': thisElem.form.action}, INPUT({'type': 'hidden', 'name': 'json_data', 'value': serializeJSON(data)}));
	getFirstElementByTagAndClassName('body').appendChild(form);
	form.submit();
	return false;
}

function getNewFieldNum(thisElem) {
	function getFieldNumInTr(tr) {
		// var inputs = findChildElements(tr, ["input[name^='presention|']"]); // name starts with "presention|"
		log('tr.className = ' + tr.className);
		var input = getFirstElementByTagAndClassName('input', '', tr);
		log('input = ' + input);
		if (input) {
			log('input.value ='+input.value);
			return (Number(input.value) + 1)
		} else {
			return 0;
		}
	}
	
	var my_tr = getFirstParentByTagAndClassName(thisElem, tagName='tr');
	var prev_tr = my_tr.previousSibling;
	while (prev_tr && prev_tr.nodeName != 'TR')
		prev_tr = prev_tr.previousSibling;
	
	var num = getFieldNumInTr(prev_tr);
	log(num);
	return numberFormatter('000')(num);
}

function addRow(thisElem, form_name) {
    var my_tr = getFirstParentByTagAndClassName(thisElem, tagName='tr');
    var name = getNameToAdd(my_tr)
    var fieldNum = getNewFieldNum(thisElem);
    var new_tr = TR({'class': 'field_row'});
    insertSiblingNodesBefore(my_tr, new_tr);
    
    new_tr.innerHTML = window['createRow' + form_name](name, fieldNum);
    fieldChooser = getFirstElementByTagAndClassName('select', '', my_tr);

    fieldChooser.remove(fieldChooser.selectedIndex);
    if (fieldChooser.length <= 0) {
        //my_tr.parentNode.removeChild(my_tr);\
        log('vypinam vysibylyty of my_tr');
        my_tr.style.visibility = 'hidden';
    }
    
    return null;
}
