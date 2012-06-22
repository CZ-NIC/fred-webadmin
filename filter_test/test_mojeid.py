# this tests following bugs:
#
#        1. child properties are ignored in request detail
#        2. missing filter for statements
#

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


#a = corba.getObject('Registry', 'MojeID')
# a = corba.getObject('Registry.MojeID.Server', 'MojeID')
a = corba.getObject('MojeID', 'Registry.MojeID')


print '---KONEC'
