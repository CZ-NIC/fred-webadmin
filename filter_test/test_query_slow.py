from omniORB.any import from_any

from fred_webadmin.corba import Corba, ccReg, Registry
from fred_webadmin.corbarecoder import CorbaRecode

import pdb;

recoder = CorbaRecode('utf-8')
c2u = recoder.decode # recode from corba string to unicode
u2c = recoder.encode # recode from unicode to strings

corba = Corba()
# corba.connect('pokuston', 'fred')
corba.connect('localhost:24846', 'fred')


a = corba.getObject('Admin', 'ccReg.Admin')
s = a.getSession(a.createSession('helpdesk'))

loggerf = s.getPageTable(ccReg.FT_LOGGER)
lfilter = loggerf.add()
loggerf.setTimeout(30000)


print 'nastavuji filtery'

di = ccReg.DateTimeInterval(
    ccReg.DateTimeType(ccReg.DateType(1, 2, 2010), 1, 0, 0),
    ccReg.DateTimeType(ccReg.DateType(7, 4, 2010), 9, 0, 0),
    ccReg.INTERVAL,
    - 1
  )

lfilter.addId()._set_value(30000000409);

#lfilter.addTimeBegin()._set_value(di)
#lfilter.addRequestType()._set_value(100);
#lfilter.addIsMonitoring()._set_value(False);
#lfilter.addServiceType()._set_value(4);


#     pdb_trace()
print 'pred reloadF()'
loggerf.reload()
print 'po reloadF()'
#     pdb_trace()

print 'HEADERS:'
print loggerf.getColumnHeaders();
#
#print '---RADKY(celkem:%s):' % loggerf._get_numRows()
#
for i in range(loggerf._get_numRows()):
    print loggerf.getRow(i);

print '---KONEC'
