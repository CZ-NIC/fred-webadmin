#!/usr/bin/env python

if __name__ == '__main__':
    from IPython import embed
    from omniORB.any import from_any

    from fred_webadmin.corba import Corba, ccReg, Registry
    from fred_webadmin.corbarecoder import CorbaRecode

    recoder = CorbaRecode('utf-8')
    c2u = recoder.decode  # recode from corba string to unicode
    u2c = recoder.encode  # recode from unicode to strings

    corba = Corba()
    corba.connect('pokuston:50001', 'fred')

    a = corba.getObject('Admin', 'ccReg.Admin')
    s = a.getSession(a.createSession('helpdesk'))
    embed()  # 'Use "a" as Admin or "s" as Session'
