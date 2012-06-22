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

mailsf = s.getPageTable(ccReg.FT_MAIL)
mfilter = mailsf.add()
mailsf.setTimeout(1)


print 'nastavuji filtery'

#di = ccReg.DateTimeInterval(
#    ccReg.DateTimeType(ccReg.DateType(28,6,2009),0,0,0),
#    ccReg.DateTimeType(ccReg.DateType(30,6,2009),0,0,0),
#    ccReg.INTERVAL,
#    -1
#  )



#pvt = mfilter.addRequestPropertyValue()
#pvt.addName()._set_value('techContact')
#pvt.addValue()._set_value('CID:ID01')


# new design proposal
# pvt = mfilter.addTable('PropertyValue', 'entry_id')
# pvt.addColumn('Name')
# pvt.addColumn('Value')



# mfilter.addActionType()._set_value('DomainCreate');
# mfilter.addIsMonitoring(false);
# pv



# raw = mfilter.addLogRawContent();
# raw.addContent()._set_value("*cvee003#08-12-05at16:31:48*")

# mfilter.addServiceType()._set_value(ccReg.LC_PUBLIC_REQUEST);

#     pdb_trace()
print 'pred reloadF()'
mailsf.reload()
print 'po reloadF()'
#     pdb_trace()

print 'HEADERS:'
print mailsf.getColumnHeaders();
#
#print '---RADKY(celkem:%s):' % mailsf._get_numRows()
#
for i in range(mailsf._get_numRows()):
    print mailsf.getRow(i);

print '---KONEC'
