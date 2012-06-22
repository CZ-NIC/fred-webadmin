"""
    Title comes here.
"""
import cherrypy
import csv
import StringIO

import fred_webadmin.corbarecoder as recoder

from logging import debug, error
from omniORB.any import from_any

from fred_webadmin.translation import _
from fred_webadmin.mappings import (
    f_name_enum, f_enum_name, f_urls, f_name_default_sort)
from fred_webadmin.corba import (
    ccReg, Registry, CorbaServerDisconnectedException)
import fred_webadmin.webwidgets.forms.emptyvalue

def fileGenerator(source, separator='|'):
    "Generates CSV stream from IterTable object"

    # CSV writer only supports files for output => we have to use StringIO.
    out = StringIO.StringIO()
    w = csv.writer(out)

    data = source.rawheader
    w.writerow([unicode(item).encode('utf-8') for item in data])
    yield out.getvalue()

    for i in xrange(source.num_rows):
        row = source[i]
        data = [col['value'] for col in row]
        out.seek(0)
        w.writerow([unicode(item).encode('utf-8') for item in data])
        # Truncate from current pos to end (if something remained
        # from the last iteration).
        out.truncate()

        # Return one line of data.
        yield out.getvalue()


class IterTable(object):
    """ Table object representing "Table"L from CORBA interface. Supports lazy
        access to rows (fetches them on demand), thus it can access very large
        data sets without running out of memory.
    """
    def __init__(self, request_object, session_key, pagesize=50, timeout=10000):
        super(IterTable, self).__init__()

        self.iterable = True
        self.request_object = request_object

        table, header_id = self._map_request(session_key)
        self._table = table
        self._table._set_pageSize(pagesize)
        self._table.setTimeout(timeout)

        columnHeaders = table.getColumnHeaders()
        self.rawheader = [x.name for x in columnHeaders]
        self.rawheader.insert(0, 'Id')

        self.header = [ _(x) for x in self.rawheader ]
        self.header_type = [x.type._n for x in columnHeaders]
        self.header_type.insert(0, header_id)

        self.page_index = None
        self.page_size = None
        self.page_start = None
        # Number of rows in table.
        self.num_rows = None
        self.num_rows_over_limit = None
        self.num_pages = None
        self.page_rows = None
        self.current_page = None
        self.first_page = None
        self.last_page = None
        self.prev_page = None
        self.next_page = None
        self._row_index = None

        self._update()

    def _map_request(self, session_key):
        try:
            debug('GETTING ADMIN, which is: %s a sessionkey=%s' %
                  (cherrypy.session.get('Admin', 'Admin'), session_key))
            corbaSession = cherrypy.session.get('Admin').getSession(session_key)
        except ccReg.Admin.ObjectNotFound:
            raise CorbaServerDisconnectedException
        try:
            debug(f_name_enum)
            table = corbaSession.getPageTable(f_name_enum[self.request_object])
            if not table:
                raise ValueError(
                    "Nonexistent PageTable for %s (corbaSession.getPageTable returned"
                    " None). This is most probably a bug on the server, so"
                    " go tell the server developers." % self.request_object)
        except KeyError:
            raise ValueError("Invalid request object.")
        header_id = 'CT_OID_ICON'
        return table, header_id

    def _update(self):
        self.page_index = self._table._get_page()
        self.page_size = self._table._get_pageSize()
        self.page_start = self._table._get_start()
        self.num_rows = self._table._get_numRows()
        self.num_rows_over_limit = self._table.numRowsOverLimit()
        self.num_pages = self._table._get_numPages()
        self.page_rows = self._table._get_numPageRows()
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

    def __len__(self):
        return self.page_rows

    def __getitem__(self, index):
        return self._get_row(index)

    def _get_row(self, index):
        row = []
        try:
            items = self._table.getRow(index)
            row_id = self.get_row_id(index)
        except Registry.Table.INVALID_ROW:
            import traceback
            raise IndexError(
                "Index %s out of bounds. Original exception: %s" % \
                (index, traceback.format_exc()))
        # Create OID from rowId.
        row_id_oid = Registry.OID(row_id, str(row_id),
                                  f_name_enum[self.request_object])
        items.insert(0, row_id_oid)
        for i, item in enumerate(items):
            cell = {}
            cell['index'] = i
            if i == 0:
                # items[0] is id (obtained from self._table.getRowId(index)).
                cell['value'] = item
            else:
                # All other items are corba ANY values.
                cell['value'] = recoder.c2u(from_any(item, True))
            self._rewrite_cell(cell)
            row.append(cell)
        return row


    def get_row_id(self, index):
        """
            Returns id of the specified row.

            Args:
                index: Index of the row.
            Returns:
                Id of the index-th row.
            Raises:
                IndexError when index is out of range.
                Usual Corba exceptions.
        """
        try:
            return self._table.getRowId(index)
        except Registry.Table.INVALID_ROW:
            import traceback
            raise IndexError(
                "Index %s out of bounds. Original exception: %s" % \
                (index, traceback.format_exc()))

    def get_rows_dict(self, start=None, limit=None, raw_header=False):
        """
            Get a specified number of rows from pagetable.

            Args:
                start: Integer. Index of the first row.
                limit: Integer. Number of rows to fetch. Defaults to pageSize.
                raw_header: Boolean. Indicates whether self.header or
                    self.raw_header names should be used as resulting dict
                    keys.
            Returns:
                Dicionary of (key: value) where key is header name (used for
                extjs grid and FilterList)
            """
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
        header = self.rawheader if raw_header else self.header
        # Make sure that limit never gets beyond bounds.
        limit = min(limit, self.num_rows - start)
        while index < start + limit:
            row = {}
            irow = self._get_row(index)
            for i, col in enumerate(irow):
                row[header[i]] = col['value']
            rows.append(row)
            index += 1
        return rows

    def get_absolute_row(self, index):
        """ Returns the specified row.

            Args:
                index: index of the row.
            Returns:
                Row with given index.
            Raises:
                IndexError when index is out of range.
                Usual Corba exceptions.
        """
        try:
            return self._table.getRow(index)
        except Registry.Table.INVALID_ROW:
            import traceback
            raise IndexError(
                "Index %s out of bounds. Original exception: %s" % \
                (index, traceback.format_exc()))

    def __iter__(self):
        """ To make IterTable iterable.
        """
        return self.next()

    def next(self):
        """ To make IterTable iterable.
        """
        while self._row_index < (self.page_start + self.page_rows):
            row = self._get_row(self._row_index)
            self._row_index += 1
            yield row
        self._row_index = self.page_start
        raise StopIteration()

    def _rewrite_cell(self, cell):
        oid_url_string = '%sdetail/?id=%s'
        rewrite_rules = {
                'CT_OID': {'oid_url': oid_url_string},
                'CT_OID_ICON': {'oid_url': oid_url_string,
                                'icon': '/img/icons/open.png'},
                'CT_OTHER': {}
            }
        contentType = self.header_type[cell['index']]

        if rewrite_rules[contentType].has_key('icon'):
            cell['icon'] = rewrite_rules[contentType]['icon']
        if rewrite_rules[contentType].has_key('oid_url'):
            val = cell['value']
            if val.id is not None and val.id and val.handle != 0:
                cell['url'] = rewrite_rules[contentType]['oid_url'] % \
                    (f_urls[f_enum_name[val.type]], val.id)
                cell['value'] = val.handle
            else:
                cell['icon'] = ''
                cell['value'] = ''
        if rewrite_rules[contentType].has_key('url'):
            cell['url'] = rewrite_rules[contentType]['url'] % (cell['value'],)

    def set_filter(self, union_filter_data):
        self.clear_filter()
        FilterLoader.set_filter(self, union_filter_data)

    def save_filter(self, name):
        self._table.saveFilter(recoder.u2c(name))

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
            # Subtract one for the ID column (see IterTable.set_sort(...)).
            col_num = self.rawheader.index(column_name) - 1
        except ValueError:
            error("Column '%s' not found in rawheader (%s)" % (column_name,
                  self.rawheader))
            raise
        self.set_sort(col_num, bool_dir)


    def set_default_sort(self):
        if f_name_default_sort.get(self.request_object):
            for column_name, direction in reversed(
                f_name_default_sort[self.request_object]):
                self.set_sort_by_name(column_name, direction)

    def get_filter_data(self):
        return FilterLoader.get_filter_data(self)

    def all_fields_filled(self):
        return FilterLoader.all_fields_filled(self)

    def clear_filter(self):
        self._table.clear()
        self._update()

    def reload(self):
        self._table.reload()
        self.set_default_sort()
        self._update()

    def load_filter(self, filter_id):
        self._table.loadFilter(filter_id)

    def set_page(self, num):
        if (self.num_pages > 0) and (num > self.num_pages):
            num = self.num_pages
        elif num <= 0:
            num = 1
        self._table.setPage(num - 1)
        self._update()

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
        for filter_data in union_filter_data:
            compound = itertable._table.add()
            cls._set_one_compound_filter(compound, filter_data)

    @classmethod
    def _set_one_compound_filter(cls, compound, filter_data):
        debug('filter_data in set_one_compound_filter: %s' % filter_data)
        for key, [neg, val] in filter_data.items():
            func = getattr(compound, "add%s" % key)
            sub_filter = func() # add

            # Follows ugly code full of 'isinstance' calls. However, it seems
            # to be necessary because we're using Corba.
            if isinstance(sub_filter, ccReg.Filters._objref_Compound): # Compound:
                cls._set_one_compound_filter(sub_filter, val)
            else:
                sub_filter._set_neg(recoder.u2c(neg))
                # Only set active filters (those that have a value).
                if not isinstance(val, fred_webadmin.webwidgets.forms.emptyvalue.FilterFormEmptyValue):
                    if isinstance(sub_filter, ccReg.Filters._objref_Date):
                        value = recoder.date_time_interval_to_corba(
                            val, recoder.date_to_corba)
                    elif isinstance(sub_filter, ccReg.Filters._objref_DateTime):
                        value = recoder.date_time_interval_to_corba(
                            val, recoder.datetime_to_corba)
                    elif isinstance(
                        sub_filter,
                        (ccReg.Filters._objref_Int, ccReg.Filters._objref_Id)):
                        value = int(val)
                    else:
                        value = val

                    sub_filter._set_value(recoder.u2c(value))

    @classmethod
    def get_filter_data(cls, itertable):
        filter_data = []
        for compound_filter in CorbaFilterIterator(itertable._table):
            filter_data.append(
                cls._get_one_compound_filter_data(compound_filter))
        return filter_data

    @classmethod
    def _get_one_compound_filter_data(cls, compound_filter):
        filter_data = {}
        for sub_filter in CorbaFilterIterator(compound_filter):
            name = recoder.c2u(sub_filter._get_name())
            debug('NAME=%s %s' % (name, type(name)))
            neg = sub_filter._get_neg()
            if isinstance(sub_filter, ccReg.Filters._objref_Compound):#Compound):
                value = cls._get_one_compound_filter_data(sub_filter)
            else:
                if sub_filter.isActive():
                    val = sub_filter._get_value()
                    debug('VALUE (from corba)=%s' % val)
                    if isinstance(sub_filter, ccReg.Filters._objref_Date):
                        value = recoder.corba_to_date_time_interval(
                            val, recoder.corba_to_date)
                    elif isinstance(sub_filter, ccReg.Filters._objref_DateTime):
                        value = recoder.corba_to_date_time_interval(
                            val, recoder.corba_to_datetime)
                    else:
                        value = recoder.c2u(val)
                else:
                    value = ''

            filter_data[name] = [neg, value]
        return filter_data

    @classmethod
    def all_fields_filled(cls, itertable):
        """ Return true when all fields are filled in (filter isActive of all
            fields is True). It ignores isActive() method in CompoundFilter
            and so recursively goes inside it.
        """
        for compound_filter in CorbaFilterIterator(itertable._table):
            if not cls._one_compound_all_fields_filled(compound_filter):
                return False
        return True

    @classmethod
    def _one_compound_all_fields_filled(cls, compound_filter):
        for sub_filter in CorbaFilterIterator(compound_filter):
            if isinstance(sub_filter, ccReg.Filters._objref_Compound):
                if not cls._one_compound_all_fields_filled(sub_filter):
                    return False
            else:
                if not sub_filter.isActive():
                    return False
        return True
