$(document).ready(function() {
    $('.confirm_submit').submit(function(e) {
        if (window.confirm("Are you sure?")) {
            return true;
        } else {
            return false;
        }
    });
});
