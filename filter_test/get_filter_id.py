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

loggerf.setTimeout(0)


print 'nastavuji filtery'

lfilter.addId()._set_value(50003633083);

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
