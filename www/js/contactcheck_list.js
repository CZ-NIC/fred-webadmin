/*
 * Administrative contact verification - check list
 */

function filter_by_testsuite_type(oSettings, aData, iDataIndex) {
    var selected_filter = $('#changelist-filter .selected').attr('id');

    if ((selected_filter == 'no-filter') || (selected_filter == 'filter-automatic' && aData[2] == 'automatic')
        || (selected_filter == 'filter-manual' && (aData[2] == 'manual' || aData[2] == 'thank_you'))) {
        return true;
    }
    return false;
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

function datetimeMRender(data, type, row) {
    if (type == 'display') {
        if (data) {
            date = new Date(Date.parse(data));
            return date.scwFormat(scwDateOutputFormat);
        }
        return '';
    }
    return data;
}

// install custom sort function
jQuery.fn.dataTableExt.oSort['null_last-asc'] = function(x, y) {
    if (x == y) {
        return 0;
    }
    if (x == "") {
        return 1;
    }
    if (y == "") {
        return -1;
    }
    if (x > y) {
        return 1;
    }
};

jQuery.fn.dataTableExt.oSort['null_last-desc'] = function(y, x) {
    if (x == y) {
        return 0;
    }
    if (x == "") {
        return 1;
    }
    if (y == "") {
        return -1;
    }
    if (x > y) {
        return 1;
    }
};

$(document)
    .ready(
        function() {
            if (typeof dontDisplayFilter === "undefined") {
                dontDisplayFilter = false;
            }
            if (typeof defaultTypeFilter === "undefined") {
                defaultTypeFilter = 'no-filter';
            }
            $('#table_tag')
                .before(
                    '<h3>Filter:</h3>\
                     <div id="changelist-filter">\
                        <label>Check type:</label>\
                        <ul>\
                            <li><a class="filter-button" id="filter-automatic">Automatic</a></li>\
                            <li><a class="filter-button" id="filter-manual">Manual</a></li>\
                            <li><a class="filter-button" id="no-filter">All</a></li>\
                        </ul>\
                     </div>');
            $('#' + defaultTypeFilter).addClass('selected');

            $('#table_tag').dataTable({
                "bProcessing" : false,
                "bPaginate" : false,
                "bFilter" : !dontDisplayFilter,
                "bInfo" : !dontDisplayFilter,
                "sAjaxSource" : ajaxSourceURLOfChecks,
                "aaSorting" : [[3, "asc"]],
                "aoColumnDefs" : [{
                    "aTargets" : [3],
                    "mRender" : datetimeMRender,
                    "sType" : "null_last"
                }, {
                    "aTargets" : [4],
                    "mRender" : datetimeMRender
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
