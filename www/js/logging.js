function log(msg) {
    if (typeof(window) != "undefined" && window.console
            && window.console.log) {
        // Safari and FireBug 0.4
        // Percent replacement is a workaround for cute Safari crashing bug
        window.console.log(msg);
    } else if (typeof(opera) != "undefined" && opera.postError) {
        // Opera
        opera.postError(msg);
    } else if (typeof(printfire) == "function") {
        // FireBug 0.3 and earlier
        printfire(msg);
    } else if (typeof(Debug) != "undefined" && Debug.writeln) {
        // IE Web Development Helper (?)
        // http://www.nikhilk.net/Entry.aspx?id=93
        Debug.writeln(msg);
    } else if (typeof(debug) != "undefined" && debug.trace) {
        // Atlas framework (?)
        // http://www.nikhilk.net/Entry.aspx?id=93
        debug.trace(msg);
    }
}