from fred_webadmin.corba import Corba, ccReg
corba = Corba()
#corba.connect('corbaname::jarahp')
corba.connect()
# recoder of CORBA objects
from fred_webadmin.corbarecoder import CorbaRecode

recoder = CorbaRecode('utf-8')
c2u = recoder.decode # recode from corba string to unicode
u2c = recoder.encode # recode from unicode to strings

admin = corba.getObject('Admin', 'Admin')
corbaSessionKey = admin.login('superuser', 'superuser123')

corbaSession = admin.getSession(corbaSessionKey)
actions = corbaSession.getEPPActions()
afilter = actions.add()

print afilter
print 'nastavuji filtery'
#afilter.addObject().addHandle()._set_value("blabla.cz")
di = ccReg.DateTimeInterval(
    ccReg.DateTimeType(ccReg.DateType(24,9,2007),0,0,0),
    ccReg.DateTimeType(ccReg.DateType(0,0,0),0,0,0),
    ccReg.DAY,
    -1
  )
afilter.addTime()._set_value(di)
print 'pred reloadF()'
actions.reloadF()
print 'po reloadF()'
print 'HEADERS:'
print actions.getColumnHeaders();

print 'RADKY(celkem:%s):' % actions._get_numRows()
#for i in range(actions._get_numRows()):
#    print actions.getRow(i);
print 'KONEC'


