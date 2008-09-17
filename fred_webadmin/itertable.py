import sys
import cherrypy
import datetime
from logging import debug, error
from omniORB.any import from_any

from corba import ccReg, Registry, CorbaServerDisconnectedException
from adif import u2c
from translation import _
from fred_webadmin.webwidgets.forms.filterforms import FilterFormEmptyValue
from fred_webadmin.mappings import f_name_enum, f_enum_name, f_header_ids, f_urls, f_name_default_sort
from fred_webadmin.utils import c2u, date_time_interval_to_corba, corba_to_date_time_interval, date_to_corba, corba_to_date, datetime_to_corba, corba_to_datetime

def fileGenerator(source, separator = '|'):
    "Generates CVS stream from IterTable object"
    data = separator.join(source.rawheader)
    yield "%s\n" % (data)
    for row in source:
        data = separator.join([col['value'] for col in row])
        yield "%s\n" % (data)
        


class IterTable(object):
    """ Table object representing "Table"L from CORBA interface. Supports lazy
        access to rows (fetches them on demand), thus it can access very large
        data sets without running out of memory.
    """
    def __init__(self, request_object, sessionKey, pagesize=50):
        debug('Creating IterTable of type %s' % request_object)
        super(IterTable, self).__init__(self)
        self.iterable = True
        self.request_object = request_object
        table, header_id = self._map_request(sessionKey)
        columnHeaders = table.getColumnHeaders()
        self.rawheader = [x.name for x in columnHeaders]
        self.rawheader.insert(0, 'Id')
        self.header = [ _(x) for x in self.rawheader ]
        self.header_type = [x.type._n for x in columnHeaders]
        self.header_type.insert(0, header_id)
        debug('HEADER=%s' % self.header)
        debug('HEADER_TYPE=%s' % self.header_type)
        self._table = table
        self._table._set_pageSize(pagesize)
        
#        self._table.reload()
        self._update()

    def _map_request(self, sessionKey):
        try:
            debug('GETTING ADMIN, which is: %s a sessionkey=%s' % (cherrypy.session.get('Admin', 'Admin'), sessionKey))
            corbaSession = cherrypy.session.get('Admin').getSession(sessionKey)
        except ccReg.Admin.ObjectNotFound:
            raise CorbaServerDisconnectedException
        #func = getattr(corbaSession, types[self.request_object]['func'])
        #table = func()
        
        #table = corbaSession.getPageTable(ccReg.FT_ACTION)#f_name_enum[self.request_object])
        table = corbaSession.getPageTable(f_name_enum[self.request_object])
        debug("Returned PageTable: %s" % table)
        header_id = 'CT_OID_ICON' #f_header_ids[self.request_object]#types[self.request_object]['id']
        return table, header_id
    
    def _update(self):
        self.page_index = self._table._get_page()
        self.page_size = self._table._get_pageSize()
        self.page_start = self._table._get_start()
        self.num_rows = self._table._get_numRows() # number of rows in table
        #self.total_rows = self._table._get_resultSize() # number of rows in database
        self.num_rows_over_limit = self._table.numRowsOverLimit()
        self.num_pages = self._table._get_numPages()
#        page_end = min(self.page_start + self.page_size, self.num_rows)
        self.page_rows = self._table._get_numPageRows()
#        if page_end > self.num_rows:
#            self._page_rows = self.page_size - (page_end - self.num_rows)
#        else:
#            self._page_rows = self.page_size
        self.current_page = self.page_index + 1
        self.first_page = 1
        self.last_page = self.num_pages
        self.prev_page = self.current_page - 1
        if self.prev_page < 1: 
            self.prev_page = self.current_page
        self.next_page = self.current_page + 1
        if self.next_page > self.last_page: 
            self.next_page = self.last_page
        self._row_index = self.page_start
            
    def __iter__(self):
        return self

    def __len__(self):
        debug("Itertable.LEN = %s" % self.page_rows)
        return self.page_rows

    def __getitem__(self, index):
        return self._get_row(index)

    def _get_row(self, index):
        row = []
        items = self._table.getRow(index)
        row_id = self._table.getRowId(index)
        row_id_oid = Registry.OID(row_id, str(row_id), f_name_enum[self.request_object])  # create OID from rowId
        items.insert(0, row_id_oid)
        for i, item in enumerate(items):
            cell = {}
            cell['index'] = i
            if i == 0: # items[0] is id, which is inserted to items (it was obtained from self._table.getRowId(index)
                cell['value'] = item
            else: # all other items are corba ANY values
                cell['value'] = c2u(from_any(item, True))
            self._rewrite_cell(cell)
            row.append(cell)
        return row

    def get_row_id(self, index):
        return self._table.getRowId(index)
    
    def get_rows_dict(self, start = None, limit = None, raw_header = False):
        ''' Get rows, where each rows is dict (key: value), where key is header name (used for extjs grid and FilterList) '''
        if start is None:
            start = self.page_start
        else:
            start = int(start)
        
        if limit is None:
            limit = self.page_size
        else:
            limit = int(limit)
            self.set_page_size(limit)
            
        rows = []
        index = start
        limit = min(limit, self.num_rows - start)
        if raw_header:
            header = self.rawheader
        else:
            header = self.header
        while index < start + limit:
            row = {}
            irow = self._get_row(index)
            for i, col in enumerate(irow):
                row[header[i]] = col['value']
            rows.append(row)
            index += 1
        return rows
    

    def get_absolute_row(self, index):
        return self._table.getRow(index)

    def next(self):
        debug("In itertable.next(), row_index: %s" % self._row_index)
        if self._row_index >= (self.page_start + self.page_rows):
            self._row_index = self.page_start
            raise StopIteration
        row = self._get_row(self._row_index)
        self._row_index += 1
        return row

    def _rewrite_cell(self, cell):
#        get_url_id_content = lambda filter_name: {'url': f_urls[filter_name] + 'detail/?id=%s',  'icon': '/img/icons/open.png', 'cssc': 'tcenter'}
#        get_url_handle_content = lambda filter_name: {'url': f_urls[filter_name] + 'detail/?handle=%s'}
        get_url_from_oid = lambda OID: {'url': f_urls[f_enum_name[OID.type]] + 'detail/?id=%s',  'icon': '/img/icons/open.png', 'cssc': 'tcenter'}
        oid_url_string = '%sdetail/?id=%s'
        rewrite_rules = {
#                        'CT_CONTACT_HANDLE': get_url_handle_content('contact'),
#                        'CT_REGISTRAR_HANDLE': get_url_handle_content('registrar'),
#                        #'CT_DOMAIN_HANDLE': {'url': f_urls['domain'] + 'detail/?handle=%s'},
#                        'CT_DOMAIN_HANDLE': get_url_handle_content('domain'),
#                        'CT_NSSET_HANDLE': get_url_handle_content('nsset'),
#                        'CT_KEYSET_HANDLE': get_url_handle_content('keyset'),
#                        'CT_CONTACT_ID': get_url_id_content('contact'),
#                        'CT_REGISTRAR_ID': get_url_id_content('registrar'),
#                        'CT_DOMAIN_ID': get_url_id_content('domain'),
#                        'CT_NSSET_ID': get_url_id_content('nsset'),
#                        'CT_KEYSET_ID': get_url_id_content('keyset'),
#                        'CT_MAIL_ID': get_url_id_content('mail'),
#                        'CT_PUBLICREQUEST_ID': get_url_id_content('publicrequest'),
#                        'CT_ACTION_ID': get_url_id_content('action'),
#                        'CT_INVOICE_ID': get_url_id_content('invoice'),
#                        #'CT_FILE_ID': {'url': f_urls['file'] + 'detail/?id=%s',  'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_OID': {'oid_url': oid_url_string},
                        'CT_OID_ICON': {'oid_url': oid_url_string, 'icon': '/img/icons/open.png'}, #{'url': f_urls['request'] + 'detail/?id=%s',  'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_OTHER': {}
                       }
        contentType = self.header_type[cell['index']]
        for key in rewrite_rules[contentType]:
            if key == 'value':
                cell['value'] = rewrite_rules[contentType]['value']
            if key == 'icon':
                cell['icon'] = rewrite_rules[contentType]['icon']
            if key == 'cssc':
                cell['cssc'] = rewrite_rules[contentType]['cssc']
            if key == 'oid_url':
                val = cell['value'] 
                cell['url'] = rewrite_rules[contentType][key] % (f_urls[f_enum_name[val.type]], val.id)
                cell['value'] = val.handle
            if key == 'url':
                cell['url'] = rewrite_rules[contentType]['url'] % (cell['value'],)



      
    def set_filter(self, union_filter_data):
        self.clear_filter()
        FilterLoader.set_filter(self, union_filter_data)
        
    def save_filter(self, name):
        self._table.saveFilter(u2c(name))
    
    def get_sort(self):
        col_num, direction = self._table.getSortedBy()
        print "SORT GETTING %s, %s" % (col_num, direction)
        return col_num, direction
    
    def set_sort(self, col_num, bool_dir):
        ''' col_num == 0 is first column AFTER ID (column ID is ignored)'''
        print "SORT SETTING %s, %s" % (col_num, bool_dir)
        self._table.sortByColumn(col_num, bool_dir)

    def set_sort_by_name(self, column_name, direction):
        bool_dir = {u'ASC': True, u'DESC': False}[direction]
        try:
            col_num = self.rawheader.index(column_name) - 1
        except ValueError:
            error('VALUEERROR is set sort, index: (header: %s, index: %s)' % (self.header, column_name))
            raise
        self.set_sort(col_num, bool_dir)
    
        
    def set_default_sort(self):
        if f_name_default_sort.get(self.request_object):
            for column_name, direction in reversed(f_name_default_sort[self.request_object]):
                self.set_sort_by_name(column_name, direction)

    def get_filter_data(self):
        return FilterLoader.get_filter_data(self)

    def all_fields_filled(self):
        return FilterLoader.all_fields_filled(self)

    def clear_filter(self):
        self._table.clear()
#        self._table.reload()
        self._update()

    def reload(self):
        debug('FILTER BEFORE RELOAD')
        #import pdb; pdb.set_trace()
        self._table.reload()
        self.set_default_sort()
        debug('FILTER AFTER RELOAD')
        self._update()
        
    def load_filter(self, filter_id):
        self._table.loadFilter(filter_id)

    def set_page(self, num):
#        import pdb; pdb.set_trace()
        if (self.num_pages > 0) and (num > self.num_pages):
            num = self.num_pages
        elif num <= 0:
            num = 1
        self._table.setPage(num - 1)
        self._update()
    
    def set_page_start(self, start):
        page_num = start % self.page_size
        self.set_page(page_num)
    

    def set_page_size(self, size):
        self._table._set_pageSize(size)
        self._update()

class CorbaFilterIterator(object):
    def __init__(self, filter_iterable):
        debug("Creating CORBAFITERATOR")
        self.iter = filter_iterable.getIterator()
        self.iter.reset()
    
    def __iter__(self):
        return self
    
    def next(self):
        debug("ITERATING NEXT, hasNext=%s" % self.iter.hasNext()) 
        if self.iter.hasNext(): #isDone()
            sub_filter = self.iter.getFilter()
            debug("iterator getFilter = :%s" % sub_filter)
            self.iter.setNext()
            return sub_filter
        else:
            raise StopIteration

class FilterLoader(object):
    @classmethod
    def set_filter(cls, itertable, union_filter_data):
        #import pdb; pdb.set_trace()
        for filter_data in union_filter_data:
            compound = itertable._table.add()
            cls._set_one_compound_filter(compound, filter_data)

    @classmethod
    def _set_one_compound_filter(cls, compound, filter_data):
        debug('filter_data in set_one_compound_filter: %s' % filter_data)
        for key, [neg, val] in filter_data.items():
            #func = getattr(compound, "add%s" % (key[0].capitalize() + key[1:])) # capitalize only first letter
            func = getattr(compound, "add%s" % key)
            sub_filter = func() # add
            debug("SUB_FILTER: %s" % sub_filter)
#            import pdb; pdb.set_trace()
            if isinstance(sub_filter, ccReg.Filters._objref_Compound): # Compound:
                cls._set_one_compound_filter(sub_filter, val)
            else:
                debug("Setting VAL %s" % val)
                sub_filter._set_neg(u2c(neg))
                if not isinstance(val, FilterFormEmptyValue): # set only filters, that are active (have value) - 
                    if isinstance(sub_filter, ccReg.Filters._objref_Date):
                        value = date_time_interval_to_corba(val, date_to_corba)
                    elif isinstance(sub_filter, ccReg.Filters._objref_DateTime):
                        value = date_time_interval_to_corba(val, datetime_to_corba)
                    elif isinstance(sub_filter, (ccReg.Filters._objref_Int, ccReg.Filters._objref_Id)):
                        value = int(val)
                    else:
                        value = val
    
                    debug('SETTING VALUE TO SUBFILTer: %s' % u2c(value))
                    sub_filter._set_value(u2c(value))
                    
                
        
    @classmethod
    def get_filter_data(cls, itertable):
        #import pdb; pdb.set_trace()
        filter_data = []
        for compound_filter in CorbaFilterIterator(itertable._table):
            filter_data.append(cls._get_one_compound_filter_data(compound_filter))
        return filter_data

    @classmethod
    def _get_one_compound_filter_data(cls, compound_filter):
        filter_data = {}
        for sub_filter in CorbaFilterIterator(compound_filter):
            name = sub_filter._get_name()
            debug('NAME=%s %s' % (name, type(name)))
            neg = sub_filter._get_neg()
            if isinstance(sub_filter, ccReg.Filters._objref_Compound):#Compound):
                value = cls._get_one_compound_filter_data(sub_filter)
            else:
                if sub_filter.isActive():
                    val = sub_filter._get_value()
                    if isinstance(sub_filter, ccReg.Filters._objref_Date):
                        value = corba_to_date_time_interval(val, corba_to_date)
                    elif isinstance(sub_filter, ccReg.Filters._objref_DateTime):
                        value = corba_to_date_time_interval(val, corba_to_datetime)
                    else:
                        value = val
                else:
                    value = ''
            
            filter_data[name] = [neg, value]
        return filter_data
    
    @classmethod
    def all_fields_filled(cls, itertable):
        ''' Return true when all fields are filled in (filter isActive of all fields is True
            It ignores isActive() method in CompoundFilter and so recursively goes inside it. 
        '''
        for compound_filter in CorbaFilterIterator(itertable._table):
            if not cls._one_compound_all_fields_filled(compound_filter):
                return False
        return True
    
    @classmethod
    def _one_compound_all_fields_filled(cls, compound_filter):
        for sub_filter in CorbaFilterIterator(compound_filter):
            if isinstance(sub_filter, ccReg.Filters._objref_Compound):#Compound):
                if not cls._one_compound_all_fields_filled(sub_filter):
                    return False
            else:
                if not sub_filter.isActive():
                    return False
        return True
                
        
        
        
