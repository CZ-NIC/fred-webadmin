import cherrypy

from corba import ccReg, CorbaServerDisconnectedException
from translation import _

def fileGenerator(source, separator = '|'):
    "Generates CVS stream from IterTable object"
    data = separator.join(source.rawheader)
    yield "%s\n" % (data)
    for row in range(source.numRows):
        data = "%s%s%s" % (source.getRowId(row), separator, separator.join(source.getAbsoluteRow(row)))
        yield "%s\n" % (data)


class IterTable(object):
    """ Table object representing "Table" from CORBA interface. Supports lazy
        access to rows (fetches them on demand), thus it can access very large
        data sets without running out of memory.
    """
    def __init__(self, requestObject, sessionKey, pagesize=50):
        super(IterTable, self).__init__(self)
        self.iterable = True
        self.requestObject = requestObject
        self.types = {'requests': {'func': 'getEPPActions', 'id': 'CT_REQUEST_ID'},
                     'registrars': {'func': 'getRegistrars', 'id': 'CT_REGISTRAR_ID'},
                     'domains': {'func': 'getDomains', 'id': 'CT_DOMAIN_ID'},
                     'nssets': {'func': 'getNSSets', 'id': 'CT_NSSET_ID'},
                     'mails': {'func': 'getMails', 'id': 'CT_MAIL_ID'},
                     'contacts': {'func': 'getContacts', 'id': 'CT_CONTACT_ID'},
                     'authinfo': {'func': 'getAuthInfoRequests', 'id': 'CT_AUTHINFO_ID'},
                     'invoices': {'func': 'getInvoices', 'id': 'CT_INVOICE_ID'}}
        table = self.__mapRequest__(requestObject, sessionKey)
        self.rawheader = [ x.name for x in table.getColumnHeaders() ]
        self.rawheader.insert(0, 'Id')
        self.header = [ _(x) for x in self.rawheader ]
        self.headerType = [ x.type._n for x in table.getColumnHeaders() ]
        self.headerType.insert(0, self.types[self.requestObject]['id'])
        self.__table = table
        self.__table._set_pageSize(pagesize)
#        self.__table.reload()
        self.__update__()

    def __iter__(self):
        return self

    def __len__(self):
        return self.__pageRows

    def __getitem__(self, index):
        print "GETTING ROW %s" % index
        return self.__getrow__(index)

    def __getrow__(self, index):
        print "_GETTING ROW %s" % index
#        import pdb; pdb.set_trace()
#        index = index + (self.__pageIndex * self.__pageSize)
        row = []
        items = self.__table.getRow(index)
        items.insert(0, str(self.__table.getRowId(index)))
        for item in enumerate(items):
            cell = {}
            cell['index'] = item[0]
            cell['value'] = item[1].decode('utf-8')
            self.__rewriteCell__(cell)
            row.append(cell)
        return row

    def getRowId(self, index):
        return self.__table.getRowId(index)

    def getAbsoluteRow(self, index):
        return self.__table.getRow(index)

    def next(self):
        print "V nextu, rowindex:", self.__rowindex
        if self.__rowindex >= (self.__pageStart + self.__pageRows):
            raise StopIteration
        row = self.__getrow__(self.__rowindex)
        self.__rowindex += 1
        return row

    def __rewriteCell__(self, cell):
        baseurl = '' #cherrypy.request.headers.get(cfg.get('html', 'header'), '')
        rewriteRules = {'CT_CONTACT_HANDLE': {'url': r'%s/contacts/detail/?handle=%%s' % baseurl},
                        'CT_REGISTRAR_HANDLE': {'url': r'%s/registrars/detail/?handle=%%s' % baseurl},
                        'CT_DOMAIN_HANDLE': {'url': r'%s/domains/detail/?handle=%%s' % baseurl},
                        'CT_NSSET_HANDLE': {'url': r'%s/nssets/detail/?handle=%%s' % baseurl},
                        'CT_CONTACT_ID': {'url': r'%s/contacts/detail/?id=%%s' % baseurl, 'value': '*', 'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_REGISTRAR_ID': {'url': r'%s/registrars/detail/?id=%%s' % baseurl, 'value': '*', 'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_DOMAIN_ID': {'url': r'%s/domains/detail/?id=%%s' % baseurl, 'value': '*', 'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_NSSET_ID': {'url': r'%s/nssets/detail/?id=%%s' % baseurl, 'value': '*', 'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_MAIL_ID': {'url': r'%s/mails/detail/?id=%%s' % baseurl, 'value': '*', 'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_AUTHINFO_ID': {'url': r'%s/authinfo/detail/?id=%%s' % baseurl, 'value': '*', 'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_REQUEST_ID': {'url': r'%s/requests/detail/?id=%%s' % baseurl, 'value': '*', 'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_INVOICE_ID': {'url': r'%s/invoices/detail/?id=%%s' % baseurl, 'value': '*', 'icon': 'list.gif', 'cssc': 'tcenter'},
                        'CT_OTHER': {}
                       }
        contentType = self.headerType[cell['index']]
        for key in rewriteRules[contentType]:
            if key == 'url':
                cell[key] = rewriteRules[contentType][key] % (cell['value'],)
            if key == 'value':
                cell[key] = rewriteRules[contentType][key]
            if key == 'icon':
                cell[key] = rewriteRules[contentType][key]
            if key == 'cssc':
                cell[key] = rewriteRules[contentType][key]

    def __mapRequest__(self, requestObject, sessionKey):
        try:
            corbaSession = cherrypy.session.get('Admin', 'Admin').getSession(sessionKey)
        except ccReg.Admin.ObjectNotFound:
            raise CorbaServerDisconnectedException
        func = getattr(corbaSession, self.types[requestObject]['func'])
        table = func()
        return table

    def __update__(self):
        self.__pageIndex = self.__table._get_page()
        self.__pageSize = self.__table._get_pageSize()
        self.__pageStart = self.__table._get_start()
        self.numRows = self.__table._get_numRows()
        self.totalRows = self.__table._get_resultSize()
        self.numPages = self.__table._get_numPages()
        pageEnd = self.__pageStart + self.__pageSize
        if pageEnd > self.numRows:
            self.__pageRows = self.__pageSize - (pageEnd - self.numRows)
        else:
            self.__pageRows = self.__pageSize
        self.current_page = self.__pageIndex + 1
        self.first_page = 1
        self.last_page = self.numPages
        self.prev_page = self.current_page - 1
        if self.prev_page < 1: 
            self.prev_page = self.current_page
        self.next_page = self.current_page + 1
        if self.next_page > self.last_page: 
            self.next_page = self.last_page
        self.__rowindex = self.__pageStart

    def __filterTable(self):
        # common for registry objects (domain, contacst and nsset)
        common = ['registrar', 'registrarHandle',
                  'createRegistrar', 'createRegistrarHandle',
                  'updateRegistrar', 'updateRegistrarHandle',
                  'crDate_start', 'crDate_end', 'crDate_day',
                  'upDate_start', 'upDate_end', 'upDate_day',
                  'trDate_start', 'trDate_end', 'trDate_day',]
        
        registrars = ['fulltext', 'name', 'handle']
        requests = ['registrar', 'registrarHandle', 'requestType', 'handle', 
                'result', 'time_start', 'time_start_hour', 'time_start_min', 
                'time_end', 'time_end_hour', 'time_end_min', 'time_day', 'clTRID', 'svTRID']
        domains = ['fqdn', 'registrant', 'registrantHandle', 
                'nsset', 'nssetHandle', 'admin', 'adminHandle', 
                'exDate_start', 'exDate_end', 'exDate_day', 
                'valExDate_start', 'valExDate_end', 'valExDate_day',
                'techAdminHandle','nssetIP']
        authinfo = ['handle', 'id', 'reason', 'email', 'authinfoStatus', 'svTRID', 'authinfoType', 
                'crTime_start', 'crTime_start_hour', 'crTime_start_min',
                'crTime_end', 'crTime_end_hour', 'crTime_end_min',
                'closeTime_start', 'closeTime_start_hour', 'closeTime_start_min',
                'closeTime_end', 'closeTime_end_hour', 'closeTime_end_min']
        contacts = ['handle', 'name', 'org', 'email', 'vat', 'ident']
        invoices = ['crDate_start', 'crDate_end', 'crDate_day',
                'taxDate_start', 'taxDate_end', 'taxDate_day',
                'number', 'registrarId', 'registrarHandle', 'zone', 'invoiceType', 
                'varSymbol', 'objectName', 'objectId', 'advanceNumber']
        mails = ['handle', 'mailFulltext', 'attachment', 'mailStatus', 'mailType', 'createTime_day',
                'createTime_start', 'createTime_start_hour', 'createTime_start_min',
                'createTime_end', 'createTime_end_hour', 'createTime_end_min']
        nssets = ['handle', 'adminHandle', 'ip', 'hostname']
        domains.extend(common)
        contacts.extend(common)
        nssets.extend(common)
        filters = {'registrars': registrars, 
                   'requests': requests, 
                   'domains': domains, 
                   'contacts': contacts, 
                   'nssets': nssets, 
                   'mails': mails, 
                   'authinfo': authinfo,
                   'invoices': invoices}
        return filters

    def setFilter(self, classname, filt):
#        print "Setting filters for '%s': %s" % (classname, str(filt))
        filters = self.__filterTable()
        f = {}.fromkeys(filters[classname], '')
        f.update(filt)
        # convert int type filters
        for key in ['registrar', 'registrarId', 'createRegistrar', 'updateRegistrar', 
                    'registrant', 'result', 'nsset', 'admin', 'id', 'mailType', 'zone',
                    'objectId', 'invoiceId']:
            if f.has_key(key):
                try:
                    f[key] = int(f[key])
                except ValueError:
                    f[key] = 0
        for key in ['crDate_start', 'crDate_end', 'crDate_day', 
                    'createDate_start', 'createDate_end', 'createDate_day', 
                    'trDate_start', 'trDate_end', 'trDate_day', 
                    'upDate_start', 'upDate_end', 'upDate_day', 
                    'exDate_start', 'exDate_end', 'exDate_day', 
                    'taxDate_start', 'taxDate_end', 'taxDate_day', 
                    'valExDate_start', 'valExDate_end', 'valExDate_day', 
                    'time_day', 'crTime_day', 'createTime_day', 'closeTime_day']:
            if f.has_key(key):
#                print "%s: '%s'" % (key, f[key])
                try:
                    f[key] = ccReg.DateType(*[int(val) for val in f[key].split('.')])
                except (TypeError, ValueError):
                    if key.endswith('_day'):
                        del(f[key])
                    else:
                        f[key] = ccReg.DateType(0, 0, 0)
        for key in ['time_start', 'time_end', 'crTime_start', 'crTime_end', 'createTime_start', 'createTime_end', 'closeTime_start', 'closeTime_end']:
            if f.has_key(key):
#                print "%s: '%s'" % (key, f[key])
                try:
                    f[key] = ccReg.DateTimeType(ccReg.DateType(*[int(val) for val in f[key].split('.')]), int(f["%s_hour" % key]), int(f["%s_min" % key]), 0)
                except (TypeError, ValueError):
                    f[key] = ccReg.DateTimeType(ccReg.DateType(0, 0, 0), 0, 0, 0)

        if f.has_key('crDate_start'):
            f['crDate'] = ccReg.DateInterval(f['crDate_start'], f['crDate_end'])
            del(f['crDate_start'])
            del(f['crDate_end'])
        if f.has_key('crDate_day'):
            f['crDate'] = ccReg.DateInterval(f['crDate_day'], f['crDate_day'])
            del(f['crDate_day'])

        if f.has_key('exDate_start'):
            f['exDate'] = ccReg.DateInterval(f['exDate_start'], f['exDate_end'])
            del(f['exDate_start'])
            del(f['exDate_end'])
        if f.has_key('exDate_day'):
            f['exDate'] = ccReg.DateInterval(f['exDate_day'], f['exDate_day'])
            del(f['exDate_day'])

        if f.has_key('taxDate_start'):
            f['taxDate'] = ccReg.DateInterval(f['taxDate_start'], f['taxDate_end'])
            del(f['taxDate_start'])
            del(f['taxDate_end'])
        if f.has_key('taxDate_day'):
            f['taxDate'] = ccReg.DateInterval(f['taxDate_day'], f['taxDate_day'])
            del(f['taxDate_day'])

        if f.has_key('valExDate_start'):
            f['valExDate'] = ccReg.DateInterval(f['valExDate_start'], f['valExDate_end'])
            del(f['valExDate_start'])
            del(f['valExDate_end'])
        if f.has_key('valExDate_day'):
            f['valExDate'] = ccReg.DateInterval(f['valExDate_day'], f['valExDate_day'])
            del(f['valExDate_day'])

        if f.has_key('upDate_start'):
            f['upDate'] = ccReg.DateInterval(f['upDate_start'], f['upDate_end'])
            del(f['upDate_start'])
            del(f['upDate_end'])
        if f.has_key('upDate_day'):
            f['upDate'] = ccReg.DateInterval(f['upDate_day'], f['upDate_day'])
            del(f['upDate_day'])

        if f.has_key('trDate_start'):
            f['trDate'] = ccReg.DateInterval(f['trDate_start'], f['trDate_end'])
            del(f['trDate_start'])
            del(f['trDate_end'])
        if f.has_key('trDate_day'):
            f['trDate'] = ccReg.DateInterval(f['trDate_day'], f['trDate_day'])
            del(f['trDate_day'])

        if f.has_key('time_start'):
            f['time'] = ccReg.DateTimeInterval(f['time_start'], f['time_end'])
            del(f['time_start'])
            del(f['time_start_hour'])
            del(f['time_start_min'])
            del(f['time_end'])
            del(f['time_end_hour'])
            del(f['time_end_min'])
        if f.has_key('time_day'):
            f['time'] = ccReg.DateTimeInterval(ccReg.DateTimeType(f['time_day'], 0, 0, 0), ccReg.DateTimeType(f['time_day'], 23, 59, 59))
            del(f['time_day'])

        if f.has_key('crTime_start'):
            f['crTime'] = ccReg.DateTimeInterval(f['crTime_start'], f['crTime_end'])
            del(f['crTime_start'])
            del(f['crTime_start_hour'])
            del(f['crTime_start_min'])
            del(f['crTime_end'])
            del(f['crTime_end_hour'])
            del(f['crTime_end_min'])
        if f.has_key('crTime_day'):
            f['crTime'] = ccReg.DateTimeInterval(ccReg.DateTimeType(f['crTime_day'], 0, 0, 0), ccReg.DateTimeType(f['crTime_day'], 23, 59, 59))
            del(f['crTime_day'])

        if f.has_key('createTime_start'):
            f['createTime'] = ccReg.DateTimeInterval(f['createTime_start'], f['createTime_end'])
            del(f['createTime_start'])
            del(f['createTime_start_hour'])
            del(f['createTime_start_min'])
            del(f['createTime_end'])
            del(f['createTime_end_hour'])
            del(f['createTime_end_min'])
        if f.has_key('createTime_day'):
            f['createTime'] = ccReg.DateTimeInterval(ccReg.DateTimeType(f['createTime_day'], 0, 0, 0), ccReg.DateTimeType(f['createTime_day'], 23, 59, 59))
            del(f['createTime_day'])

        if f.has_key('closeTime_start'):
            f['closeTime'] = ccReg.DateTimeInterval(f['closeTime_start'], f['closeTime_end'])
            del(f['closeTime_start'])
            del(f['closeTime_start_hour'])
            del(f['closeTime_start_min'])
            del(f['closeTime_end'])
            del(f['closeTime_end_hour'])
            del(f['closeTime_end_min'])
        if f.has_key('closeTime_day'):
            f['closeTime'] = ccReg.DateTimeInterval(ccReg.DateTimeType(f['closeTime_day'], 0, 0, 0), ccReg.DateTimeType(f['closeTime_day'], 23, 59, 59))
            del(f['closeTime_day'])

        if f.has_key('requestResult'):
            f['resultClass'] = ccReg.EPPActionsFilter.ResultType._item(int(f['requestResult']))
            del(f['requestResult'])

        if f.has_key('requestType'):
            f['type'] = f['requestType']
            del(f['requestType'])

        if f.has_key('authinfoStatus'):
            f['status'] = ccReg.AuthInfoRequest.RequestStatus._item(int(f['authinfoStatus']))
            del(f['authinfoStatus'])

        if f.has_key('authinfoType'):
            f['type'] = ccReg.AuthInfoRequest.RequestType._item(int(f['authinfoType']))
            del(f['authinfoType'])

        if f.has_key('mailStatus'):
            try:
                f['status'] = int(f['mailStatus'])
            except:
                f['status'] = -1
            del(f['mailStatus'])

        if f.has_key('mailFulltext'):
            f['fulltext'] = f['mailFulltext']
            del(f['mailFulltext'])

        if f.has_key('mailType'):
            f['type'] = f['mailType']
            del(f['mailType'])

        if f.has_key('invoiceType'):
            f['type'] = ccReg.Invoicing.Invoices[int(f['invoiceType'])]['obj']
            del(f['invoiceType'])

        for key, val in f.items():
#            print "%s: '%s', %s" % (key, val, type(val))
            try:
                func = getattr(self.__table, "_set_%s" % (key))
                func(val)
            except:
                print "************** EXCEPTION on: IterTable.setFilter(%s)" % key
#                raise
        self.__table.reload()
        self.__update__()

    def clearFilter(self):
        self.__table.clear()
        self.__table.reload()
        self.__update__()

    def reload(self):
        self.__table.reload()
        self.__update__()

    def setPage(self, num):
#        import pdb; pdb.set_trace()
        if (self.numPages > 0) and (num > self.numPages):
            num = self.numPages
        elif num <= 0:
            num = 1
        self.__table.setPage(num - 1)
        self.__update__()

    def setPageSize(self, size):
        self.__table._set_pageSize(size)
#        self.__table.reload()
        self.__update__()

