/*
 * Administrative contact verification - check list
 */

function filter_by_testsuite_type(oSettings, aData, iDataIndex) {
    var selected_filter = $('#changelist-filter .selected').attr('id');

    if (selected_filter != 'no-filter') {
        test_suite_handle = selected_filter.substring(7, selected_filter.length);
        if (aData[2] == test_suite_handle) {
            return true;
        }
        return false;
    }
    return true;
}

function set_selected_filter_button(button) {
    var clicked_button_id = $(button).attr('id');
    $('.filter-button').each(function(index) {
        var button = $(this);
        if (button.attr('id') == clicked_button_id) {
            button.addClass('selected');
        } else {
            button.removeClass('selected');
        }
    });
    $('#table_tag').dataTable().fnDraw();
}

$(document)
    .ready(
        function() {
            $('#table_tag')
                .before(
                    '<h2>Filter:</h2>\
                     <div id="changelist-filter">\
                        <label>Check type:</label>\
                        <ul>\
                            <li><a class="filter-button selected" id="no-filter">All</a></li>\
                            <li><a class="filter-button" id="filter-automatic">Automatic</a></li>\
                            <li><a class="filter-button" id="filter-manual">Manual</a></li>\
                        </ul>\
                    </div>');
            $('#table_tag').dataTable({
                "bProcessing" : false,
                "bPaginate" : false,
                "sAjaxSource" : '/contactcheck/json_filter/',
                "aaSorting" : [[3, "desc"]],
                "aoColumnDefs" : [{
                    "aTargets" : [3],
                    "mRender" : function(data, type, row) {
                        if (data) {
                            date = new Date(Date.parse(data));
                            return date.scwFormat(scwDateOutputFormat);
                        }
                        return '';
                    }
                }, {
                    "aTargets" : [4],
                    "mRender" : function(data, type, row) {
                        date = new Date(Date.parse(data));
                        return date.scwFormat(scwDateOutputFormat);
                    }
                }]
            });
            $('#no-filter').click(function() {
                set_selected_filter_button(this);
            });
            $('#filter-automatic').click(function() {
                set_selected_filter_button(this);
            });
            $('#filter-manual').click(function() {
                set_selected_filter_button(this);
            });
            $.fn.dataTableExt.afnFiltering.push(filter_by_testsuite_type);
        });
