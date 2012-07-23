Ext.ItertablesPagingToolbar = Ext.extend(Ext.PagingToolbar, {
    /* overrides updateInfo to expect 4 arguments in displayMsg string (added num_row_in_db as last argument) */
    updateInfo : function() {
        if(this.displayEl){
            var count = this.store.getCount();
            var msg = count == 0 ?
                this.emptyMsg :
                String.format(
                    this.displayMsg,
                    this.cursor+1, this.cursor+count, this.store.getTotalCount(), this.store.reader.jsonData.num_rows_in_db
                );
            this.displayEl.update(msg);
        }
    }/*,
    getPageData : function(){
        var total = this.store.getTotalCount();
        var ap  =   Math.ceil((this.cursor+this.pageSize)/this.pageSize);
        if (this.store.reader.jsonData.start ) {
            // go to the specified page
            ap  =   Math.ceil((this.store.reader.jsonData.start + this.pageSize)/this.pageSize);
            // also set the cursor so that 'prev' and 'next' buttons behave correctly
            this.cursor =   this.store.reader.jsonData.start;
        }
        return {
            total : total,
            activePage : ap,
            pages :  total < this.pageSize ? 1 : Math.ceil(total/this.pageSize)
        };
    }*/
});


var IterTableUI = function() {
    var store; //hold our data
    var grid; //component
    var cm; // definition of the columns
    var header = 'nenastaveno'; //json header informations
    var headerType = 'nenast'; //json header type informations
    var pageSize;
    var pageIndex;
    var objectName;
    var totalInDB;

    function setupDataSource() {
        // create the Data Store
        log('header pred create Store:' + Ext.encode(header));
        store = new Ext.data.Store({
            proxy: new Ext.data.HttpProxy({
                url: './jsondata'
            }),

            reader: new Ext.data.JsonReader({
                //start: 'start', // have to be 'start', because of ItertablesPagingToolbar.getPageData count on that
                totalProperty: 'num_rows',
                totalInDB: 'num_rows_in_db',
                root: 'rows',
                id: 'Id', // id must be unique identifier of row
                fields: header /*[
                    'id'/*'title', 'forumtitle', 'forumid', 'author',
                    {name: 'replycount', type: 'int'},
                    {name: 'lastpost', mapping: 'lastpost', type: 'date', dateFormat: 'timestamp'},
                    'lastposter', 'excerpt'
                ]*/
            }),

            // turn on remote sorting
            remoteSort: true
        });
        //store.setDefaultSort('Id', 'ASC');

        store.load();

        window.store = store;

    }


    // pluggable renders
    function renderTopic(value, p, record) {
        return String.format(
                '<b><a href="http://extjs.com/forum/showthread.php?t={2}" target="_blank">{0}</a></b><a href="http://extjs.com/forum/forumdisplay.php?f={3}" target="_blank">{1} Forum</a>',
                value, record.data.forumtitle, record.id, record.data.forumid);
    }
    function renderLast(value, p, r){
        return String.format('{0}<br/>by {1}', value.dateFormat('M j, Y, g:i a'), r.data['lastposter']);
    }
    function renderIDFunc(objectName) {
        return function(value) {
            if (value && value != '0') {
                return '<a href="/' + objectName + '/detail/?id=' + value + '"><img src="/img/icons/open.png" /></a>';
            } else {
                return 'N/A';
            }
        };
    }
    function renderHandleFunc(objectName) {
        return function(value) {
            return '<a href="/' + objectName + '/detail/?handle=' + value + '">' + value + '</a>';
        };
    }

    // the column model has information about grid columns
    // dataIndex maps the column to the specific data field in
    // the data store
    function getColumnModel() {
        if(!cm && header) {
            var colsSpec = [];
            log(header);
            log(header.length);
            for (var i = 0; i < header.length; i++) {
                log(i);
                var colHeader = header[i];
                var colHeaderType = headerType[i];
                log(colHeader,colHeaderType)
                var colSpec = {
                    header: colHeader,
                    dataIndex: colHeader
                }
                colSpec['width'] = 130;
                if (colHeaderType.substr(colHeaderType.length - '_ID'.length) == '_ID') {// endsWith('_ID')
                    colSpec['sortable'] = false;
                    colSpec['width'] = 30;
                    //colSpec['hidden'] = true;
                }
                var reHandle = new RegExp(/CT_([^_]*)_HANDLE/);
                var reId     = new RegExp(/CT_([^_]*)_ID/);
                var match;
                if (match = reHandle.exec(colHeaderType)) {
                    var obj_name = match[1]; // first matching group
                    colSpec['renderer'] = renderHandleFunc(obj_name.toLowerCase());
                } else if (match = reId.exec(colHeaderType)) {
                    var obj_name = match[1]; // first matching group
                    colSpec['renderer'] = renderIDFunc(obj_name.toLowerCase());
                }
                /*switch (colHeaderType) {
                    case 'CT_ACTION_ID':
                        colSpec['renderer'] = renderIDFunc('action');
                        break;

                    case 'CT_DOMAIN_HANDLE':
                        colSpec['renderer'] = renderHandleFunc('domain');
                        break;

                    case 'CT_REGISTRAR_HANDLE':
                        colSpec['renderer'] = renderHandleFunc('registrar');
                        break;

                    //here are special renderers
                    default:;
                }*/

                colsSpec.push(colSpec);
            }
            log('colsSpec:' + Ext.encode(colsSpec));
            cm = new Ext.grid.ColumnModel(colsSpec);
            /*cm = new Ext.grid.ColumnModel([{
                   header: 'id',
                   dataIndex: 'id',
                   renderer: function(val){if (val) {return '<a href="./detail?id=' + val + '" >id</a>'} else {return 'bezcislacico'}}
                },{
                   id: 'topic', // id assigned so we can apply custom css (e.g. .x-grid-col-topic b { color:#333 })
                   header: "Topic",
                   dataIndex: 'title',
                   width: 420,
                   renderer: renderTopic
                },{
                   header: "Author",
                   dataIndex: 'author',
                   width: 100,
                   hidden: true
                },{
                   header: "Replies",
                   dataIndex: 'replycount',
                   width: 70,
                   align: 'right'
                },{
                   id: 'last',
                   header: "Last Post",
                   dataIndex: 'lastpost',
                   width: 150,
                   renderer: renderLast
                }]);
            }*/
            cm.defaultSortable = true;
        }
    }


    function buildGrid() {

        grid = new Ext.grid.GridPanel({
            el:'div_for_itertable',
            //width:700,
            height:700,
            //autoExpandColumn:'common',
            //autoHeight: true,
            //autoScroll: true,
            //title:'',
            store: store,
            cm: cm,
            //viewConfig:{forceFit: true},
            //trackMouseOver:false,
            //sm: new Ext.grid.RowSelectionModel({selectRow:Ext.emptyFn}),
            //sm: new Ext.grid.CellSelectionModel(),//{selectRow:Ext.emptyFn}),
            //disableSelection: true,
            loadMask: true,
            bbar: new Ext.ItertablesPagingToolbar({
                pageSize: pageSize,
                store: store,
                displayInfo: true,
                displayMsg: 'Displaying results {0} - {1} of {2} ({3})',
                emptyMsg: "No results to display"
                /*items:[
                    '-', {
                    pressed: true,
                    enableToggle:true,
                    text: 'Show Preview',
                    cls: 'x-btn-text-icon details',
                    toggleHandler: toggleDetails
                }]*/
            })
        });

        //grid.on('beforeColMenuShow', setCSSExtjsMenu);
        // render it
        grid.render();
        /*grid.bottomToolbar.displayMsg = 'Displaying results {0} - {1} of {2} blabla'
        grid.store.on('beforeload', function (store) {
            grid.bottomToolbar.displayMsg = 'Displaying results {0} - {1} of {2} (' + store.reader.jsonData.num_rows_in_db + ')';
        });*/
        grid.getView().colMenu.getEl().addClass('extjs');
        grid.getView().hmenu.getEl().addClass('extjs');
        window.grid = grid;
        //grid.on('rowclick', function(grid, rowNum) {location.href='/' + objectName + '/detail/?id=' + grid.getStore().getAt(rowNum)['id']});

    }

    function getHeaderAndSetupGrid() {
        //log(header);
        //log(header_type);
        Ext.Ajax.request({
            url: './jsonheader',
            success: function (result, request) {
                //Ext.MessageBox.alert('Success', 'Data return from the server: '+ result.responseText);
                result = Ext.decode(result.responseText);

                header = result['header'];
                headerType = result['header_type'];
                pageSize = result['page_size'];
                objectName = result['object_name'];
                setupDataSource();
                getColumnModel();
                buildGrid();
            },
            failure: function (result, request) {
                Ext.MessageBox.alert('Failed', 'Retrieving header failed.');
            }
        });
    }
    function setCSSExtjsMenu() {
        // sets all elements with css class x-menu css class extjs
        log('nazdar bazar csss menu')
        Ext.select('.x-menu').addClass('extjs');
    }
    /*function toggleDetails(btn, pressed){
        var view = grid.getView();
        view.showPreview = pressed;
        view.refresh();
    } */

    return {
        // trigger the data store load
        init: function() {
            getHeaderAndSetupGrid();
        },

        getDataStore: function() {
            return store;
        }
    }


}();

Ext.onReady(IterTableUI.init, IterTableUI, true);
