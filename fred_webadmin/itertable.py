import cherrypy
import datetime

from corba import ccReg, CorbaServerDisconnectedException
from adif import u2c
from translation import _

def fileGenerator(source, separator = '|'):
    "Generates CVS stream from IterTable object"
    data = separator.join(source.rawheader)
    yield "%s\n" % (data)
    for row in range(source.num_rows):
        data = "%s%s%s" % (source.get_row_id(row), separator, separator.join(source.get_absolute_row(row)))
        yield "%s\n" % (data)
        


class IterTable(object):
    """ Table object representing "Table"L from CORBA interface. Supports lazy
        access to rows (fetches them on demand), thus it can access very large
        data sets without running out of memory.
    """
    def __init__(self, request_object, sessionKey, pagesize=50):
        print "VYTVARIM iTABLE"
        super(IterTable, self).__init__(self)
        self.iterable = True
        self.request_object = request_object
        table, header_id = self._map_request(sessionKey)
        self.rawheader = [ x.name for x in table.getColumnHeaders() ]
        self.rawheader.insert(0, 'Id')
        self.header = [ _(x) for x in self.rawheader ]
        self.header_type = [ x.type._n for x in table.getColumnHeaders() ]
        self.header_type.insert(0, header_id)
        print 'HEADER=%s' % self.header
        print 'HEADER_TYPE=%s' % self.header_type
        self._table = table
        self._table._set_pageSize(pagesize)
        
#        self._table.reload()
        self._update()

    def _map_request(self, sessionKey):
        types = {'requests': {'func': 'getEPPActions', 'id': 'CT_REQUEST_ID'},
                     'registrars': {'func': 'getRegistrars', 'id': 'CT_REGISTRAR_ID'},
                     'domains': {'func': 'getDomains', 'id': 'CT_DOMAIN_ID'},
                     'nssets': {'func': 'getNSSets', 'id': 'CT_NSSET_ID'},
                     'mails': {'func': 'getMails', 'id': 'CT_MAIL_ID'},
                     'contacts': {'func': 'getContacts', 'id': 'CT_CONTACT_ID'},
                     'authinfo': {'func': 'getAuthInfoRequests', 'id': 'CT_AUTHINFO_ID'},
                     'invoices': {'func': 'getInvoices', 'id': 'CT_INVOICE_ID'}}
        try:
            print "GETTING ADMIN, ktery je:", cherrypy.session.get('Admin', 'Admin')
            corbaSession = cherrypy.session.get('Admin').getSession(sessionKey)
        except ccReg.Admin.ObjectNotFound:
            raise CorbaServerDisconnectedException
        func = getattr(corbaSession, types[self.request_object]['func'])
        table = func()
        header_id = types[self.request_object]['id']
        return table, header_id
    
    def _update(self):
        self.page_index = self._table._get_page()
        self.page_size = self._table._get_pageSize()
        self.page_start = self._table._get_start()
        self.num_rows = self._table._get_numRows() # number of rows in table
        self.total_rows = self._table._get_resultSize() # number of rows in database
        self.num_pages = self._table._get_numPages()
        page_end = min(self.page_start + self.page_size, self.num_rows)
        self._page_rows = page_end - self.page_start 
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
        print "Itertable.LEN = ", self._page_rows
        return self._page_rows

    def __getitem__(self, index):
        return self._get_row(index)

    def _get_row(self, index):
        row = []
        items = self._table.getRow(index)
        items.insert(0, str(self._table.getRowId(index)))
        for item in enumerate(items):
            cell = {}
            cell['index'] = item[0]
            cell['value'] = item[1].decode('utf-8')
            self._rewrite_cell(cell)
            row.append(cell)
        return row

    def get_row_id(self, index):
        return self._table.getRowId(index)
    
    def get_rows(self, start, limit):
        index = start
        limit = min(limit, self.total_rows)
        while index < start + limit:
            yield self.get_row_id(index)
            
    def get_rows_dict(self, start = None, limit = None):
        ''' Get rows, where each rows is dict (key: value), where key is header name (used for extjs grid) '''
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
        print "limit = min(limit, self.num_rows - start)", limit, ' = min(%s, %s - %s = %s)' % (limit, self.num_rows, start, self.total_rows - start) 
        limit = min(limit, self.num_rows - start)
        header = self.header
        while index < start + limit:
            print index, start + limit
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
        print "V nextu, row_index:", self._row_index
        if self._row_index >= (self.page_start + self._page_rows):
            raise StopIteration
        row = self._get_row(self._row_index)
        self._row_index += 1
        return row

    def _rewrite_cell(self, cell):
        baseurl = '' #cherrypy.request.headers.get(cfg.get('html', 'header'), '')
        rewrite_rules = {'CT_CONTACT_HANDLE': {'url': r'%s/contacts/detail/?handle=%%s' % baseurl},
                        'CT_REGISTRAR_HANDLE': {'url': r'%s/registrars/detail/?handle=%%s' % baseurl},
                        'CT_DOMAIN_HANDLE': {'url': r'%s/domains/detail/?handle=%%s' % baseurl},
                        'CT_NSSET_HANDLE': {'url': r'%s/nssets/detail/?handle=%%s' % baseurl},
                        'CT_CONTACT_ID': {'url': r'%s/contacts/detail/?id=%%s' % baseurl,  'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_REGISTRAR_ID': {'url': r'%s/registrars/detail/?id=%%s' % baseurl,  'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_DOMAIN_ID': {'url': r'%s/domains/detail/?id=%%s' % baseurl,  'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_NSSET_ID': {'url': r'%s/nssets/detail/?id=%%s' % baseurl,  'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_MAIL_ID': {'url': r'%s/mails/detail/?id=%%s' % baseurl,  'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_AUTHINFO_ID': {'url': r'%s/authinfos/detail/?id=%%s' % baseurl,  'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_REQUEST_ID': {'url': r'%s/requests/detail/?id=%%s' % baseurl,  'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_INVOICE_ID': {'url': r'%s/invoices/detail/?id=%%s' % baseurl,  'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_OTHER': {}
                       }
        contentType = self.header_type[cell['index']]
        for key in rewrite_rules[contentType]:
            if key == 'url':
                cell[key] = rewrite_rules[contentType][key] % (cell['value'],)
            if key == 'value':
                cell[key] = rewrite_rules[contentType][key]
            if key == 'icon':
                cell[key] = rewrite_rules[contentType][key]
            if key == 'cssc':
                cell[key] = rewrite_rules[contentType][key]


      
    def set_filter(self, union_filter_data):
        FilterLoader.set_filter(self, union_filter_data)

        print "FILTER PRED RELOAD"
        self._table.reloadF()
        print "FILTER PO RELOAD"
        self._update()

    def set_sort(self, column_name, direction):
        bool_dir = {u'ASC': True, u'DESC': False}[direction]
        try:
            col_num = self.header.index(column_name) - 1 # - 1 because of headers are with ID, but in corba server without ID
        except ValueError:
            print 'VALUEERROR pri index: (header: %s, index: %s)' % (self.header, column_name)
            raise
        self._table.sortByColumn(col_num, bool_dir)

    def get_filter_data(self):
        return FilterLoader.get_filter_data(self)

    def clear_filter(self):
        t_iter = self._table.getIterator()
        t_iter.clearF()
        self._table.clear()
#        self._table.clearF()
#        self._table.reload()
#        self._table.reloadF()
        self._update()

    def reload(self):
#        self._table.reload()
        self._table.reloadF()
        self._update()

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
        print "VYTVARIM CORBAFITERATOR"
        self.iter = filter_iterable.getIterator()
        self.iter.reset()
    
    def __iter__(self):
        return self
    
    def next(self):
        print "ITERUJU NEXT, hasNext=", self.iter.hasNext() 
        if self.iter.hasNext(): #isDone()
            sub_filter = self.iter.getFilter()
            print "iterator vraci:", sub_filter
            self.iter.setNext()
            return sub_filter
        else:
            raise StopIteration

class FilterLoader(object):
    
    @staticmethod
    def date_to_corba(date):
        'parametr date is datetime.date() or None, and is converted to ccReg.DateType. If date is None, then ccReg.DateType(0, 0, 0) is returned' 
        return date and ccReg.DateType(*reversed(date.timetuple()[:3])) or ccReg.DateType(0, 0, 0)
    @staticmethod
    def corba_to_date(corba_date):
        return datetime.date(corba_date.year, corba_date.month, corba_date.day)
    
    @staticmethod
    def datetime_to_corba(date_time):
        if date_time:
            t_tuple = date_time.timetuple()
            return ccReg.DateTimeType(ccReg.DateType(*reversed(t_tuple[:3])), *t_tuple[3:6])
        else:
            return ccReg.DateTimeType(ccReg.DateType(0, 0, 0), 0, 0, 0)
    
    @staticmethod
    def corba_to_datetime(corba_date_time):
        corba_date = corba_date_time.date
        if corba_date.year == 0: # empty date is in corba = DateType(0, 0, 0)
            return None
        return datetime.datetime(corba_date.year, corba_date.month, corba_date.day, 
                                 corba_date_time.hour, corba_date_time.minute, corba_date_time.second)
    
        
    @classmethod
    def date_time_interval_to_corba(cls, val, date_conversion_method):
        '''
        val is list, where first three values are ccReg.DateType or ccReg.DateTimeType, according to that, 
        it should be called with date_coversion_method cls.date_to_corba or cls.date_time_interval_to_corba,
        next in list is offset and ccReg.DateTimeIntervalType
        '''
        if date_conversion_method == cls.date_to_corba:
            interval_type = ccReg.DateInterval
        else:
            interval_type = ccReg.DateTimeInterval
        print 'date_conversion_method', date_conversion_method
        c_from, c_to, c_day = [date_conversion_method(date) for date in val[:3]]
        if int(val[3]) == ccReg.DAY._v: 
            corba_interval = interval_type(c_day, c_to, ccReg.DAY, val[4] or 0) # c_to will be ignored
        else:
            corba_interval = interval_type(c_from, c_to, ccReg.DateTimeIntervalType._items[val[3]], val[4] or 0)
        return corba_interval

    @classmethod
    def corba_to_date_time_interval(cls, val, date_conversion_method):
        if val.type == ccReg.DAY:
            return [None, None, date_conversion_method(val._from), val.type._v, 0]
        elif val.type == ccReg.INTERVAL:
            return [date_conversion_method(val._from), date_conversion_method(val.to), None, val.type._v, 0]
        else:
            return [None, None, None, val.type._v, val.offset]
                    
    @classmethod
    def set_filter(cls, itertable, union_filter_data):
        for filter_data in union_filter_data:
            compound = itertable._table.add()
            cls._set_one_compound_filter(compound, filter_data)

    @classmethod
    def _set_one_compound_filter(cls, compound, filter_data):
        print 'filter_data v set:', filter_data
        for key, [neg, val] in filter_data.items():
            key = key[len(u'filter|'):] # all names starts with 'filter|'  
            func = getattr(compound, "add%s" % (key[0].capitalize() + key[1:])) # capitalize only first letter
            sub_filter = func()
            print "SUB_FILTER:", sub_filter
#            import pdb; pdb.set_trace()
            if isinstance(sub_filter, ccReg.Filters._objref_Compound):#Compound):
                cls._set_one_compound_filter(sub_filter, val)
            else:
                if isinstance(sub_filter, ccReg.Filters._objref_Date):
                    value = cls.date_time_interval_to_corba(val, cls.date_to_corba)
                elif isinstance(sub_filter, ccReg.Filters._objref_DateTime):
                    value = cls.date_time_interval_to_corba(val, cls.datetime_to_corba)
                elif isinstance(sub_filter, ccReg.Filters._objref_Int):
                    value = int(val)
                else:
                    value = val

                print "SETTING VALUE TO USBFILTer:", u2c(value)
                sub_filter._set_value(u2c(value))
                sub_filter._set_neg(u2c(neg))
                
        
    @classmethod
    def get_filter_data(cls, itertable):
        filter_data = []
        for compound_filter in CorbaFilterIterator(itertable._table):
            filter_data.append(cls._get_one_compound_filter_data(compound_filter))
        return filter_data

    @classmethod
    def _get_one_compound_filter_data(cls, compound_filter):
        filter_data = {}
        for sub_filter in CorbaFilterIterator(compound_filter):
            name = sub_filter._get_name()
            neg = sub_filter._get_neg()
            if isinstance(sub_filter, ccReg.Filters._objref_Compound):#Compound):
                value = cls._get_one_compound_filter_data(sub_filter)
            else:
                val = sub_filter._get_value()
                print 'NAME=', name, type(name)
                if isinstance(sub_filter, ccReg.Filters._objref_Date):
                    value = cls.corba_to_date_time_interval(val, cls.corba_to_date)
                elif isinstance(sub_filter, ccReg.Filters._objref_DateTime):
                    value = cls.corba_to_date_time_interval(val, cls.corba_to_datetime)
                else:
                    value = val
            
            filter_data['filter|' + name] = [neg, value]
        return filter_data
            
            
                
        
        
        
