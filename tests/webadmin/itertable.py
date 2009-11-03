import mox
import cherrypy
import CORBA
import omniORB

from nose.tools import with_setup, raises
from fred_webadmin.corba import Registry

import fred_webadmin.itertable
from fred_webadmin.itertable import IterTable

test_type_corba_enum = 42

""" Inject "test_req_object" into mapping. """
fred_webadmin.itertable.f_name_enum = {}
fred_webadmin.itertable.f_name_enum["test_req_object"] = test_type_corba_enum

fred_webadmin.itertable.f_enum_name = {}
fred_webadmin.itertable.f_enum_name[test_type_corba_enum] = "test_req_object"

fred_webadmin.itertable.f_urls = {}
fred_webadmin.itertable.f_urls["test_req_object"] = "www.test.foo/baz/"


class TestItertable(object):

    def __init__(self):
        self.corba_mock = None
        self.admin_mock = None
        self.session_mock = None
        self.pagetable_mock = None

    def setup(self):
        self.corba_mock = mox.Mox()
        # Create admin mock and add it to cherrypy.session
        self.admin_mock = self.create_admin_mock()
        cherrypy.session = {}
        cherrypy.session['Admin'] = self.admin_mock
        # Create session mock
        self.session_mock = self.corba_mock.CreateMockAnything()
        self.admin_mock.getSession("test_ses_key").InAnyOrder(
            "setup").AndReturn(self.session_mock)
        # Create pagetable mock
        self.pagetable_mock = self.create_pagetable_mock()
        self.session_mock.getPageTable(test_type_corba_enum).AndReturn(
            self.pagetable_mock)

    def init_itertable(self, pagetable_mock, numPages=1, numPageRows=10):
        """ Provide methods for a pagetable mock that are called by
            Itertable.__init__. Those methods can be called in any order
            (pagetable behaves like a stub during the initialization).
        """
        pagetable_mock.getColumnHeaders().InAnyOrder("init pt").AndReturn(
            [Registry.Table.ColumnDesc("col1", Registry.Table.CT_OTHER),
             Registry.Table.ColumnDesc("col2", Registry.Table.CT_OTHER)])
        pagetable_mock._set_pageSize(50).InAnyOrder("init pt")
        pagetable_mock._get_page().InAnyOrder("init pt").AndReturn(1)
        pagetable_mock._get_pageSize().InAnyOrder("init pt").AndReturn(100)
        pagetable_mock._get_start().InAnyOrder("init pt").AndReturn(1)
        pagetable_mock._get_numRows().InAnyOrder("init pt").AndReturn(10)
        pagetable_mock.numRowsOverLimit().InAnyOrder("init pt").AndReturn(50)
        pagetable_mock._get_numPages().InAnyOrder("init pt").AndReturn(numPages)
        pagetable_mock._get_numPageRows().InAnyOrder(
            "init pt").AndReturn(numPageRows)

    def create_pagetable_mock(self):
        pagetable_mock = self.corba_mock.CreateMockAnything()
        pagetable_mock.__str__ = lambda : "pagetable mock"
        return pagetable_mock

    def create_admin_mock(self):
        admin_mock = self.corba_mock.CreateMockAnything()
        admin_mock.__str__ = lambda : "admin mock"
        return admin_mock

    @with_setup(setup)
    def test_init(self):
        """ IterTable initializes correctly. """
        self.init_itertable(self.pagetable_mock)
        
        self.corba_mock.ReplayAll()

        table = IterTable("test_req_object", "test_ses_key", pagesize=50)

        assert table is not None

        self.corba_mock.VerifyAll()

    @raises(ValueError)
    @with_setup(setup)
    def test_init_unknown_request_object(self):
        """ IterTable throws KeyError when request_object is not known. """
        self.init_itertable(self.pagetable_mock)
        self.corba_mock.ReplayAll()
        table = IterTable("test_invalid_req_object", "test_ses_key", 
                          pagesize=50)

    @with_setup(setup)
    def test__get_row(self):
        """_get_row returns row correctly. """
        self.init_itertable(self.pagetable_mock)
        self.pagetable_mock.getRow(2).AndReturn([CORBA.Any(CORBA.TC_string,
                                                 'test value')])
        self.pagetable_mock.getRowId(2).AndReturn(1)

        self.corba_mock.ReplayAll()
        table = IterTable("test_req_object", "test_ses_key", pagesize=50)
        row = table._get_row(2)

        assert len(row) == 2
        assert row[1]['value'] == 'test value'
        

    @raises(CORBA.BAD_PARAM)
    @with_setup(setup)
    def test__get_row_out_of_index(self):
        """ _get_row raises an exception when index is out of range. """
        self.init_itertable(self.pagetable_mock, numPages=1, numPageRows=1)

        self.pagetable_mock.getRow(2).AndRaise(
            CORBA.BAD_PARAM(omniORB.BAD_PARAM_PythonValueOutOfRange, 
                            CORBA.COMPLETED_NO))
        self.pagetable_mock.getRowId(2).AndReturn(1)

        self.corba_mock.ReplayAll()
        table = IterTable("test_req_object", "test_ses_key", pagesize=50)
        table._get_row(2)


    @raises(CORBA.BAD_PARAM)
    @with_setup(setup)
    def test__get_row_out_of_index(self):
        """ _get_row raises an exception when index is not an integer. """
        self.init_itertable(self.pagetable_mock, numPages=1, numPageRows=1)

        self.pagetable_mock.getRow("error - this should be an integer").\
            AndRaise(CORBA.BAD_PARAM(omniORB.BAD_PARAM_PythonValueOutOfRange, 
                     CORBA.COMPLETED_NO))
        self.pagetable_mock.getRowId(2).AndReturn(1)

        self.corba_mock.ReplayAll()
        table = IterTable("test_req_object", "test_ses_key", pagesize=50)
        table._get_row("error - this should be an integer")
