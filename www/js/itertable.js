var IterTableUI = function() { 
    var store; //hold our data
    var grid; //component
    var cm; // definition of the columns
    var header = 'nenastaveno'; //json header informations
    var headerType = 'nenast'; //json header type informations
    var pageSize;
   
    function setupDataSource() {
	    // create the Data Store
        log('header pred create Store:' + Ext.encode(header));
	    store = new Ext.data.Store({
	        proxy: new Ext.data.HttpProxy({            
	            url: './jsondata'
	        }),
	
	        reader: new Ext.data.JsonReader({
	            totalProperty: 'num_rows',
	            //totalInDB: 'num_rows_in_db',
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
    }
    
            

    // pluggable renders
    function renderTopic(value, p, record){
        return String.format(
                '<b><a href="http://extjs.com/forum/showthread.php?t={2}" target="_blank">{0}</a></b><a href="http://extjs.com/forum/forumdisplay.php?f={3}" target="_blank">{1} Forum</a>',
                value, record.data.forumtitle, record.id, record.data.forumid);
    }
    function renderLast(value, p, r){
        return String.format('{0}<br/>by {1}', value.dateFormat('M j, Y, g:i a'), r.data['lastposter']);
    }
    function renderIDFunc(object_name) {
        return function(value) {
            return '<a href="/' + object_name + '/detail?id=' + value + '">ID</a>';
        };
    }
    function renderHandleFunc(object_name) {
        return function(value) {
            return '<a href="/' + object_name + "/detail?handle='" + value + '">ID</a>';
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
                    dataIndex: colHeader,
                }
                
                switch (colHeaderType) {
                    case 'CT_REQUEST_ID':
                        colSpec['renderer'] = renderIDFunc('requests');
                        colSpec['sortable'] = false;
                        
                    /*case 'CT_DOMAIN_HANDLE':
                        colSpec['renderer'] = renderHandleFunc('domain');*/
                        
                    //here are special renderers
                    default:;
                }
                
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
	        //height:500,
            autoHeight: true,
	        //title:'',
	        store: store,
	        cm: cm,
            //viewConfig:{forceFit: true},
	        trackMouseOver:false,
	        //sm: new Ext.grid.RowSelectionModel({selectRow:Ext.emptyFn}),
            sm: new Ext.grid.CellSelectionModel(),//{selectRow:Ext.emptyFn}),
            //disableSelection: true,
	        loadMask: true,
	        bbar: new Ext.PagingToolbar({
	            pageSize: pageSize,
	            store: store,
	            displayInfo: true,
	            displayMsg: 'Displaying results {0} - {1} of {2}',
	            emptyMsg: "No results to display",
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
        grid.getView().colMenu.getEl().addClass('extjs');
        grid.getView().hmenu.getEl().addClass('extjs');
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