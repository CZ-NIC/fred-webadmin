function setHistory(checkbox) {
    Ext.Ajax.request({
        url: '/set_history',
        method: 'POST',
        params: {"history": checkbox.checked},
        success: function (result, request) {
            //alert('History set to ' + checkbox.checked);
            //if (location.host.search('glinic') != -1) alert('History set to ' + checkbox.checked);
            if (location.pathname.search('/detail') != -1) location.reload()
        },
        failure: function (result, request) {
            alert('Communication with server failed.');
            checkbox.checked = !checkbox.checked;
        }
    })
}
