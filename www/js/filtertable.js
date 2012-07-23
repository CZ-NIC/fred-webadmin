function composedNameLessThan(composeName1, composeName2) {
    //composed name less than (according to order (fieldNum) in allFieldsDict)
    var names1 = composeName1.split('-');
    var names2 = composeName2.split('-');
    var formName = filterObjectName;
    var fields = allFieldsDict[formName]; // filterObjectName is global variable created in UnionFilterFormLayout
    var i = 0;
    while (true) {
        var num1 = fields[names1[i]].fieldNum
        var num2 = fields[names2[i]].fieldNum
        log('num1 < num2 =' + num1 + '<' + num2 + '=' + num1 < num2);
        if (num1 < num2) {
            return true;
        } else if (num1 > num2) {
            return false;
        }
        log(fields[names1[i]].formName);
        fields = allFieldsDict[fields[names1[i]].formName];
        i++;
    }
}

function fieldPresented(ftable, composedName) {
    // log('volam fieldPresented(', ftable, ',', composedName, ')');
    var result = false;
    var trs = ftable.select('.field_row').elements;
    for (var i = 0; i < trs.length; i++) {
        var tr = trs[i];
        if (tr.className.split(' ')[1] == composedName) {
            return true;
        }
    }
    return result;
}

function createFieldRow(ftable, formName, composedName, composedLabel, filterName) {
    function insertRowToTable(newFieldTr) {
        var fieldRows = ftable.select('.field_row');
        if (fieldRows.getCount()) {
            for (var i = 0, len = fieldRows.getCount(); i < len; i++) {
                var fieldRow = fieldRows.item(i);
                var rowComposedName = fieldRow.dom.className.split(' ')[1];
                if (composedNameLessThan(composedName, rowComposedName)) {
                    fieldRow.insertSibling(newFieldTr, 'before');
                    return;
                }
                fieldRow.insertSibling(newFieldTr, 'after');
            }
        } else {
            ftable.select('.filtertable_header').item(0).insertSibling(newFieldTr, 'after');
        }
    }

    log('createFieldRow formName = "' + formName + '"');
    var fieldTr = new Ext.Element(document.createElement('tr'));
    fieldTr.set({'class': 'field_row ' + composedName});
    var createCommand = 'createRow' + formName + '("' + filterName + '", "' + composedLabel + '");';
    log('createCommand:' + createCommand);
    var fieldTrInnerHTML = eval(createCommand);
    log(fieldTrInnerHTML);


    /*var previousTr = ftable.select('.field_row').last();
    if (!previousTr)
        previousTr = ftable.select('.filtertable_header');
    previousTr.insertSibling(fieldTr, 'after');*/
    insertRowToTable(fieldTr);

    fieldTr.update(fieldTrInnerHTML);
    fieldTr.highlight();
}

function fieldMenuItemCheck(menuItem, checked) {
    log('clicknul jsem na menuItem' + menuItem.text + 'ktere je checked =' +
         checked + 'a jeho composedName =' + menuItem.composedName);

    if (checked) { // create new row
        createFieldRow(menuItem.ftable, menuItem.formName, menuItem.composedName, menuItem.composedLabel, menuItem.filterName);
    } else { // delete exiting row
        var fieldTr = menuItem.ftable.select('.' + menuItem.composedName).item(0);
        fieldTr.remove();
    }
}

function getFilterFieldsByComposedName(composedName) {
    var formName = filterObjectName
    var fields = allFieldsDict[formName]; // filterObjectName is global variable created in UnionFilterFormLayout

    if (composedName) {
        var names = composedName.split('-');
        log('names:' + names);
        for (var i = 0; i < names.length; i++) {
            var name = names[i];
            log('name:' + name);
            formName = fields[name].formName;
            fields = allFieldsDict[formName];
        }
    }
    return [fields, formName];
}

function getFormMenu(ftable, composedName, composedLabel) {
    // return menu items for last level in composedName
    // if composedName not specified, menu of filterObjectName is returned
    var menuItems = [];

    var fields, parentFormName;
    //[fields, parentFormName] = getFilterFieldsByComposedName(composedName); //doesn't work in fucking IE
    var fieldsAndFormName = getFilterFieldsByComposedName(composedName);
    fields = fieldsAndFormName[0];
    parentFormName =fieldsAndFormName[1];

    log('fields: ' + Ext.encode(fields));

    for (var filterName in fields) {
        log('filterName:' + filterName);
        var fieldRec = fields[filterName];
        var formName = fieldRec['formName'];
        var filterLabel = fieldRec['label'];
        var menuItem;
        if (formName)
            menuItem = new Ext.menu.Item();
        else
            menuItem = new Ext.menu.CheckItem();
        menuItem.text = filterLabel;

        menuItem.filterName = filterName;
        menuItem.hideOnClick = false;
        menuItem.composedName = (composedName ? (composedName + '-') : '') + filterName;
        menuItem.composedLabel = (composedLabel ? (composedLabel + '.') : '') + filterLabel;
        menuItem.ftable = ftable;
        menuItem.formName = parentFormName;
        if (formName) { // is compound
            menuItem.on('beforerender', fieldMenuItemBeforeRender);
            // ['beforerender'] = fieldMenuItemBeforeRender
        } else {
            log(menuItem.composedName + 'neni compound, takze mu davam checked');
            log('fieldPresented(' + ftable + ', ' + menuItem.composedName+') = ' + fieldPresented(ftable, filterName))
            menuItem.checked = fieldPresented(ftable, menuItem.composedName);
            menuItem.on('checkchange', fieldMenuItemCheck);
        }
        menuItems.push(menuItem);
    }

    return new Ext.menu.Menu( {
        items : menuItems,
        cls: 'extjs',
        defaults : {
            hideOnClick : false
        }
    });
}

function fieldMenuItemBeforeRender(menuItem) {
    log('volame fieldMenuItemBeforeRender menuItem.text = ' + menuItem.text);
    menuItem.menu = getFormMenu(menuItem.ftable, menuItem.composedName, menuItem.composedLabel);
}

function addFilterButton(ftable) {
    var fieldButtonTd = ftable.select('.for_fields_button').elements[0];
    log('pridavam button do ' + fieldButtonTd);
    var menu = getFormMenu(ftable)
    button = new Ext.Button( {
        text : 'Fields',
        menu : menu,
        renderTo : fieldButtonTd
    });
}

function addFieldsButtons() {
    Ext.select('.filtertable', true).each(addFilterButton);
}

function formContentToObject(formContent) {
    var obj = {};
    var keys = formContent[0];
    var vals = formContent[1];
    for (var i = 0; i < keys.length; i++) {
        var key = keys[i];
        var val = vals[i];
        if (obj[key] == undefined) {
            obj[key] = val;
        } else { // for example multi-select have more values under same key,
                    // so we'll create array and pushing values to it
            var prev_val = obj[key];
            if (!(prev_val instanceof Array))
                obj[key] = [prev_val]
            obj[key].push(val)
        }
    }
    return obj;
}

/*function delRow(thisElem, fieldName, fieldLabel) {
    var tr = getFirstParentByTagAndClassName(thisElem, 'tr');

    // add field back to field chooser and make field chooser visible
    var select = findChildElements(tr.parentNode,
            ['> tr.and_row > td > select'])[0];
    select.options[select.options.length] = new Option(fieldLabel, fieldName);
    var fieldChooserTr = getFirstParentByTagAndClassName(select, tagName = 'tr');
    fieldChooserTr.style.visibility = 'visible';

    // and finally remove field
    tr.parentNode.removeChild(tr);
}*/

/*function getNameToAdd(tr) {
    // get name of field, which will be added in addRow*
    var fieldChooser = getFirstElementByTagAndClassName('select', '', tr);
    return fieldChooser.value
}*/

function addOrForm(thisElem) {
    thisElem = Ext.get(thisElem);
    var my_tr = thisElem.parent('tr');
    var or_tr = new Ext.Element(document.createElement('tr'));
    or_tr.set({'class' : 'or_row'});
    var form_tr = new Ext.Element(document.createElement('tr'));;

    my_tr.insertSibling(or_tr, 'before');
    my_tr.insertSibling(form_tr, 'before');
    or_tr.dom.innerHTML = buildOrRow();
    form_tr.dom.innerHTML = buildForm();
    addFilterButton(Ext.get(form_tr));
}

function removeOr(thisElem) {
    var myTr = Ext.get(thisElem).findParent('tr', true, true);
    var formTr = myTr.next();
    myTr.remove();
    formTr.remove();
}

function getFieldRowData(fieldRow) {
    var rowData = {};

    //var innerFTable = findChildElements(fieldRow, ['.filtertable'])[0];
    /*if (innerFTable) { // compound field
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
    } else {*/
        rowData = formContentToObject(formContents(fieldRow.dom));
    /*}*/
    log('j_rowData = ' + Ext.encode(rowData));
    return rowData;
}

function getFTableData(ftable, ftData) {
    var ftData = {}; // {} is same as (now deprecated): new Object();
    var fieldRows = ftable.select('.field_row');
    log('fieldRows.length = ' + fieldRows.getCount());
    for (var j = 0, len = fieldRows.getCount(); j < len; j++) {
        var fieldRow = fieldRows.item(j);
        var rowData = getFieldRowData(fieldRow);
        var composedName = fieldRow.dom.className.split(' ')[1];
        var names = composedName.split('-');
        var dataRec = ftData;
        for (var i = 0; i < names.length; i++) {
            var name = names[i];

            if (i == names.length - 1) { //this is the last name in composedName
                Ext.apply(dataRec, rowData);
            } else { //this is not the last name in composedName (it is compound filter)
                if (!dataRec[name]) { // if data object for this subfilter doesn't exist, create one
                    dataRec[name] = {};
                    dataRec['presention|' + name] = 'on';
                }
                dataRec = dataRec[name];
            }
        }
    }
    // update(ft_data, {'ahoj': 'cau'})
    log('ftData:' + Ext.encode(ftData));
    return ftData
}

function sendUnionForm(thisElem, saveName) {
    var thisForm;
    if (thisElem.nodeName == 'FORM')
        thisForm = thisElem;
    else
        thisForm = thisElem.form;

    var data = [];
    var ftables = Ext.get(thisForm).select('.unionfiltertable > tbody > tr > td > .filtertable');
    for (var i = 0, len = ftables.getCount(); i < len; i++) {
        var ftable = ftables.item(i);
        ftdata = getFTableData(ftable)
        log('Do data pushuju ftdata:' + Ext.encode(ftdata));
        data.push(ftdata);
        log('data po pushu: ' + Ext.encode(data));
    }
    log('union form DATA:' + Ext.encode(data));
    var form = new Ext.Element(document.createElement('form'))
    form.set({
        'method' : 'post',
        'action' : thisForm.action,
        'style' : 'display: none'
    });
    var dataInput = new Ext.Element(document.createElement('input'));
    dataInput.set({
        'type' : 'hidden',
        'name' : 'json_data',
        'value' : Ext.encode(data),
        'style' : 'display: none'
    });
    form.appendChild(dataInput)
    if (saveName) {
        saveInput = new Ext.Element(document.createElement('input'));
        saveInput.set({
            'type' : 'hidden',
            'name' : 'save_input',
            'value' : saveName,
            'style' : 'display: none'
        });
        form.appendChild(saveInput);
    }
    Ext.getBody().appendChild(form);
    form.dom.submit();
    return false;
}

function saveUnionForm(thisElem) {
    var thisEl = Ext.get(thisElem);
    saveEdit = thisEl.prev()
    if (saveEdit.dom.disabled) {
        saveEdit.dom.disabled = false;
        saveEdit.dom.style.display = 'inline';
        saveEdit.focus();
        saveEdit.dom.select();
        return false;
    } else {
        sendUnionForm(thisElem, saveEdit.dom.value);
    }
}

/*function getFTableDataOld(ftable) {
    var ftData = {}; // {} is same as (now deprecated): new Object();
    var fieldRows = findChildElements(ftable, ['> tbody > tr.field_row']);
    log('fieldRows.length = ' + fieldRows.length);
    for (var i = 0; i < fieldRows.length; i++) {
        var fieldRow = fieldRows[i];
        update(ftData, getFieldRowData(fieldRow));
    }
    // update(ft_data, {'ahoj': 'cau'})
    return ftData
}*/

/*function sendUnionFormOld(thisElem) {
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
    // var form = FORM({'method':'post'}, INPUT({'type': 'hidden', 'name':
    // 'data', 'value': encodeURIComponent(serializeJSON(data))}));
    var form = FORM({
        'method' : 'post',
        'action' : this.form.action
    }, INPUT( {
        'type' : 'hidden',
        'name' : 'json_data',
        'value' : serializeJSON(data)
    }));
    getFirstElementByTagAndClassName('body').appendChild(form);
    form.submit();
    return false;
}*/

/*function getNewFieldNum(thisElem) {
    function getFieldNumInTr(tr) {
        // var inputs = findChildElements(tr, ["input[name^='presention|']"]);
        // // name starts with "presention|"
        log('tr.className = ' + tr.className);
        var input = Ext.query('input', tr)[0];

        log('input = ' + input);
        if (input) {
            log('input.value = ' + input.value);
            return (Number(input.value) + 1)
        } else {
            return 0;
        }
    }

    var my_tr = getFirstParentByTagAndClassName(thisElem, tagName = 'tr');
    var prev_tr = my_tr.previousSibling;
    while (prev_tr && prev_tr.nodeName != 'TR')
        prev_tr = prev_tr.previousSibling;

    var num = getFieldNumInTr(prev_tr);
    log(num);
    return numberFormatter('000')(num);
}*/

/*function addRow(thisElem, form_name) {
    var my_tr = getFirstParentByTagAndClassName(thisElem, tagName = 'tr');
    var name = getNameToAdd(my_tr)
    var fieldNum = getNewFieldNum(thisElem);
    var new_tr = TR( {
        'class' : 'field_row'
    });
    insertSiblingNodesBefore(my_tr, new_tr);

    new_tr.innerHTML = window['createRow' + form_name](name, fieldNum);
    var fieldChooser = getFirstElementByTagAndClassName('select', '', my_tr);

    fieldChooser.remove(fieldChooser.selectedIndex);
    if (fieldChooser.length <= 0) {
        // my_tr.parentNode.removeChild(my_tr);\
        log('vypinam vysibylyty of my_tr');
        my_tr.style.visibility = 'hidden';
    }

    return null;
}*/
