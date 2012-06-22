from omniORB.any import from_any

from fred_webadmin.corba import Corba, ccReg, Registry
from fred_webadmin.corbarecoder import CorbaRecode


recoder = CorbaRecode('utf-8')
c2u = recoder.decode # recode from corba string to unicode
u2c = recoder.encode # recode from unicode to strings


corba = Corba()
corba.connect('jsadek', 'fred-tom')

a = corba.getObject('Admin', 'ccReg.Admin')
s = a.getSession(a.createSession('helpdesk'))
