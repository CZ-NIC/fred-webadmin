$(document).ready(function() {
    $('.status_col input[type=radio]').change(function() {
        var parent_tr = $(this).closest('tr');
        parent_tr.removeClass('status_fail status_ok');
        if ($(this).val() == 'ok') {
            parent_tr.addClass('status_ok');
        } else if ($(this).val() == 'fail') {
            parent_tr.addClass('status_fail');
        }
    });
});
