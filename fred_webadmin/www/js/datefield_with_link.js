function setDateFieldPlusMonths(dateField) {
    var newDate = new Date();
    newDate.setMonth(newDate.getMonth() + parseInt(dateField.attr('data-add-months-count')));
    dateField.val(newDate.scwFormat(scwDateOutputFormat));
}

$(document).ready(
    function() {
        $("input[data-add-months-count]").each(
            function(index) {
                var dateField = $(this);
                dateField.after($(
                    '<span class="date-add-months-link link-style" href="#">'
                        + dateField.attr('data-add-months-link-text') + '</span>').click(function() {
                    setDateFieldPlusMonths(dateField);
                }));
            });
    });
