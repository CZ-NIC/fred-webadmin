import cherrypy

from fred_webadmin import config
from fred_webadmin.adif import u2c, c2u
from fred_webadmin.corba import Corba, ccReg
#from sys import stderr as err

login, password = 'superuser', 'superuser123'


class TestFilterLoader:
    def __init__(self):
        self.admin = None
        self.corbaSession = None
        
    def setup(self):
    #    err.writeln("setup module done")
#        err.write('SetUp module\n')
        ior=config.iors[0]
        corba = Corba()
        corba.connect(ior)
        
        self.admin = corba.getObject('Admin', 'Admin')
        self.corbaSession = self.admin.login(u2c(login), u2c(password))
        print "Setting admin to session, ktery je:", self.admin
        cherrypy.session = {'Admin': self.admin}
        print "hnedGETTING ADMIN, ktery je:", cherrypy.session.get('Admin')
        corbaSession = cherrypy.session.get('Admin').getSession(self.corbaSession)
#        err.write("SetUp module done\n")
    
    def teardown(self):
        pass
#        err.write("TearDown module\n")
#        err.write("TearDown module done\n")
        
    def test_filter_loader(self):
        'Tests filter loader - create, save to severver and load back a filter' 
        from fred_webadmin.itertable import IterTable, FilterLoader
        
        
        print 'printing'
        input_filter_data = [{u'object': [False, {u'handle': [False, u'test.cz']}]}, {u'registrar': [False, {u'handle': [True, u'REG-FRED_A']}]}]
        
        itable = IterTable('actions', self.corbaSession)
        print "SET FILTERS:"
        FilterLoader.set_filter(itable, input_filter_data)
        print "GET FILTERS DATA:"
        output_filter_data = FilterLoader.get_filter_data(itable)
#        dom = self.admin.getDomainById(38442)
        assert input_filter_data == output_filter_data, 'This should be same:\n' + str(input_filter_data) + '\n' + str(output_filter_data)
        

