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
s=a.getSession(a.createSession('helpdesk'))



# additions : 

# pdb.set_trace()

loggerf = s.getPageTable(ccReg.FT_LOGGER)
lfilter = loggerf.add()


print 'nastavuji filtery'
#lfilter.addObject().addHandle()._set_value("blabla.cz")
# only one day 12. - 13.  dunno why

#di = ccReg.DateTimeInterval(
#    ccReg.DateTimeType(ccReg.DateType(28,6,2009),0,0,0),
#    ccReg.DateTimeType(ccReg.DateType(30,6,2009),0,0,0),
#    ccReg.INTERVAL,
#    -1 
#  )

di = ccReg.DateTimeInterval(
    ccReg.DateTimeType(ccReg.DateType(7,3,2010),1,0,0),
    ccReg.DateTimeType(ccReg.DateType(7,3,2010),9,0,0),
    ccReg.INTERVAL,
    -1
  )

lfilter.addTimeBegin()._set_value(di)


#pv = lfilter.addRequestPropertyValue()
#pv.addName()._set_value('rc')
#pv.addValue()._set_value('2305')



#pvt = lfilter.addRequestPropertyValue()
#pvt.addName()._set_value('techContact')
#pvt.addValue()._set_value('CID:ID01')


# 

# new design proposal
# pvt = lfilter.addTable('PropertyValue', 'entry_id') 
# pvt.addColumn('Name')
# pvt.addColumn('Value')



# lfilter.addActionType()._set_value('DomainCreate');
# lfilter.addIsMonitoring(false);
# pv



# raw = lfilter.addLogRawContent();
# raw.addContent()._set_value("*cvee003#08-12-05at16:31:48*")

# lfilter.addServiceType()._set_value(ccReg.LC_PUBLIC_REQUEST);

#print 'pred reloadF()'
#loggerf.reload()
#print 'po reloadF()'
#print 'HEADERS:'
#print loggerf.getColumnHeaders();
#
#print '---RADKY(celkem:%s):' % loggerf._get_numRows()
#
#for i in range(loggerf._get_numRows()):
#    print loggerf.getRow(i);
#

print s.getDetail(ccReg.FT_LOGGER, 4)
print
#print s.getDetail(ccReg.FT_LOGGER, 22)
#print
#print s.getDetail(ccReg.FT_LOGGER, 847)
#print
#print s.getDetail(ccReg.FT_LOGGER, 848)
#print 
#

print '---KONEC'



