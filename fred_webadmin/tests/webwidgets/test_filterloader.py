import cherrypy

from fred_webadmin import config
from fred_webadmin.controller.adif import recoder
u2c = recoder.u2c
c2u = recoder.c2u
#from fred_webadmin import corba
from fred_webadmin.corba import Corba, ccReg
#from sys import stderr as err

login, password = 'superuser', 'superuser123'


class TestFilterLoader(object):
    def __init__(self):
        self.admin = None
        self.corbaSession = None

    def setup(self):
        corba = Corba()
        corba.connect()

        self.admin = corba.getObject('ccReg.Admin', 'ccReg.Admin')
        self.admin.authenticateUser(u2c(login), u2c(password))
        self.corbaSessionString = self.admin.createSession(u2c(login))

        cherrypy.session = {'Admin': self.admin}

    def teardown(self):
        pass

    def test_filter_loader(self):
        'Tests filter loader - create, save to severver and load back a filter'
        from fred_webadmin.itertable import IterTable, FilterLoader


        print 'printing'
        input_filter_data = [{u'object': [False, {u'handle': [False, u'test.cz']}]}, {u'registrar': [False, {u'handle': [True, u'REG-FRED_A']}]}]

        itable = IterTable('action', self.corbaSessionString)
        print "SET FILTERS:"
        FilterLoader.set_filter(itable, input_filter_data)
        print "GET FILTERS DATA:"
        output_filter_data = FilterLoader.get_filter_data(itable)
#        dom = self.admin.getDomainById(38442)
        assert input_filter_data == output_filter_data, 'This should be same:\n' + str(input_filter_data) + '\n' + str(output_filter_data)
