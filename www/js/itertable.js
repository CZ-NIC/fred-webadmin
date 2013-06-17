function addSelectAllBlockingCheckbox() {
    if (document.getElementById('itertable_selection_form')) {
        console.log('BLOKOVANI');
        var id_header_cell = document.getElementById('id_column_header_cell');
        var select_all_checkbox = document.createElement('input');
        select_all_checkbox.id = 'select_all_checkbox';
        select_all_checkbox.type = 'checkbox';
        id_header_cell.insertBefore(select_all_checkbox, id_header_cell.firstChild);
        Ext.select('#select_all_checkbox').on('change', select_all_checkbox_onchange);
        Ext.select('.object_selection').on('change', object_selection_checkbox_onchange);
    }
}

function select_all_checkbox_onchange(event) {
    console.log('new_value:' + event.target.checked);
    Ext.select('.object_selection').each(function(object_selection_checkbox) {
        object_selection_checkbox.dom.checked = event.target.checked;
    });
}

function object_selection_checkbox_onchange(event) {
    var all_checked = true;
    Ext.select('.object_selection').each(function(object_selection_checkbox) {
        if (!object_selection_checkbox.dom.checked) {
            all_checked = false;
            return false; // break from the each "cycle"
        }
    });
    document.getElementById('select_all_checkbox').checked = all_checked;
}

Ext.onReady(addSelectAllBlockingCheckbox);
