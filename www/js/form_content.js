function formContents(elem/* = document.body */) {
	function processElement(elem) {
	    /* Recursive function for processing element and putting form data into `names' and `values'*/
        var name = elem.name;
        if (name) {
            var tagName = elem.tagName.toUpperCase();
            if (tagName === "INPUT"
                && (elem.type == "radio" || elem.type == "checkbox")
                && !elem.checked
            ) {
                return null;
            }
            if (tagName === "SELECT") {
                if (elem.type == "select-one") {
                    if (elem.selectedIndex >= 0) {
                        var opt = elem.options[elem.selectedIndex];
                        var v = opt.value;
                        if (!v) {
                            var h = opt.outerHTML;
                            // internet explorer sure does suck.
                            if (h && !h.match(/^[^>]+\svalue\s*=/i)) {
                                v = opt.text;
                            }
                        }
                        names.push(name);
                        values.push(v);
                        return null;
                    }
                    // no form elements?
                    names.push(name);
                    values.push("");
                    return null;
                } else {
                    var opts = elem.options;
                    if (!opts.length) {
                        names.push(name);
                        values.push("");
                        return null;
                    }
                    for (var i = 0; i < opts.length; i++) {
                        var opt = opts[i];
                        if (!opt.selected) {
                            continue;
                        }
                        var v = opt.value;
                        if (!v) {
                            var h = opt.outerHTML;
                            // internet explorer sure does suck.
                            if (h && !h.match(/^[^>]+\svalue\s*=/i)) {
                                v = opt.text;
                            }
                        }
                        names.push(name);
                        values.push(v);
                    }
                    return null;
                }
            }
            names.push(name);
            values.push(elem.value || '');
        }
        for (var i = 0; i < elem.childNodes.length; i++) {
            child = elem.childNodes[i];
            processElement(child);
        }
    }

    var names = [];
    var values = [];
    if (typeof(elem) == "undefined" || elem === null) {
        elem = document.body;
    } else {
        elem = Ext.getDom(elem);
    }
    processElement(elem);
    log('formContents returning: ' + Ext.encode([names, values]));
    return [names, values];
}
