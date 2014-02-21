/*
 * Administrative contact verification - check list
 */

$(document).ready(function() {
    $('#table_tag').dataTable({
        "bProcessing" : true,
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
});
