import mox
import cherrypy
import CORBA
import omniORB

from nose.tools import with_setup, raises
from fred_webadmin.corba import Registry, ccReg

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

# Fake session string for Corba session
test_corba_session_string = "test_ses_key"


class Initializer(object):
    """
        Utility class for preventing boilerplate code.
        TODO(tomas): Probably may not be be a class at all.
    """

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
        self.admin_mock.getSession(test_corba_session_string).InAnyOrder(
            "setup").AndReturn(self.session_mock)
        # Create pagetable mock
        self.pagetable_mock = self.create_pagetable_mock()

    def init_itertable(self, pagetable_mock, columnDesc=None, page=1, 
                       pageSize=5, start=1, numRows=50, numPages=10, 
                       numPageRows=5, rowsOverLimit=False):
        """ Utility method to prevent boilerplate code.
            Provides methods that are called by Itertable.__init__. 
            Those methods can be called in any order (pagetable_mock behaves
            like a stub during the initialization).
        """
        if columnDesc is None:
            columnDesc = ["col1", "col2"]
        self.session_mock.getPageTable(test_type_corba_enum).AndReturn(
            self.pagetable_mock)
        pagetable_mock.getColumnHeaders().InAnyOrder("init pt").AndReturn(
            [Registry.Table.ColumnDesc(desc, Registry.Table.CT_OTHER) for 
             desc in columnDesc])
        pagetable_mock._set_pageSize(50)
        self.itertable_update(pagetable_mock, page, pageSize, start, numRows,
                          numPages, numPageRows, rowsOverLimit)
       
    def itertable_update(self, pagetable_mock, page=1, pageSize=5, start=1,
                     numRows=50, numPages=10, numPageRows=5,
                     rowsOverLimit=False):
        """ Utility method to prevent boilerplate code.
            Simulates IterTable._update method. """
        pagetable_mock._get_page().InAnyOrder("update pt").AndReturn(page)
        pagetable_mock._get_pageSize().InAnyOrder("update pt").AndReturn(
            pageSize)
        pagetable_mock._get_start().InAnyOrder("update pt").AndReturn(start)
        pagetable_mock._get_numRows().InAnyOrder("update pt").AndReturn(numRows)
        pagetable_mock.numRowsOverLimit().InAnyOrder(
            "update pt").AndReturn(rowsOverLimit)
        pagetable_mock._get_numPages().InAnyOrder("update pt").AndReturn(
            numPages)
        pagetable_mock._get_numPageRows().InAnyOrder(
            "update pt").AndReturn(numPageRows)


    def create_pagetable_mock(self):
        pagetable_mock = self.corba_mock.CreateMockAnything()
        # Necessary for possible debug prints in the code.
        pagetable_mock.__str__ = lambda : "pagetable mock"
        return pagetable_mock

    def create_admin_mock(self):
        admin_mock = self.corba_mock.CreateMockAnything()
        # Necessary for possible debug prints in the code.
        admin_mock.__str__ = lambda : "admin mock"
        return admin_mock


class TestItertable(Initializer):
    def __init__(self):
        Initializer.__init__(self)

    @with_setup(Initializer.setup)
    def test_init(self):
        """ IterTable initializes correctly. """
        self.init_itertable(self.pagetable_mock)
        
        self.corba_mock.ReplayAll()

        table = IterTable("test_req_object", test_corba_session_string, pagesize=50)

        assert table is not None
        self.corba_mock.VerifyAll()

    @raises(ValueError)
    @with_setup(Initializer.setup)
    def test_init_unknown_request_object(self):
        """ IterTable throws KeyError when request_object is not known. """
        self.init_itertable(self.pagetable_mock)
        self.corba_mock.ReplayAll()
        table = IterTable("test_invalid_req_object", test_corba_session_string, 
                          pagesize=50)
        self.corba_mock.VerifyAll()


class Test_getRow(Initializer):
    def __init__(self):
        Initializer.__init__(self)

    @with_setup(Initializer.setup)
    def test__get_row(self):
        """_get_row returns row correctly. """
        self.init_itertable(self.pagetable_mock)
        self.pagetable_mock.getRow(2).AndReturn([CORBA.Any(CORBA.TC_string,
                                                 'test value')])
        self.pagetable_mock.getRowId(2).AndReturn(12)

        self.corba_mock.ReplayAll()
        table = IterTable("test_req_object", test_corba_session_string, pagesize=50)
        row = table._get_row(2)

        assert len(row) == 2

        assert row[0]['url'] == "www.test.foo/baz/detail/?id=12"
        assert row[0]['index'] == 0
        assert row[0]['icon'] is not None

        assert row[1]['index'] == 1
        assert row[1]['value'] == 'test value'

        self.corba_mock.VerifyAll()

    @raises(IndexError)
    @with_setup(Initializer.setup)
    def test__get_row_out_of_index(self):
        """ _get_row raises IndexError when index is out of range. """
        self.init_itertable(self.pagetable_mock, numPages=1, numPageRows=1)

        self.pagetable_mock.getRow(2).AndRaise(
            CORBA.BAD_PARAM(omniORB.BAD_PARAM_PythonValueOutOfRange, 
                            CORBA.COMPLETED_NO))
        self.pagetable_mock.getRowId(2).AndReturn(1)

        self.corba_mock.ReplayAll()
        table = IterTable("test_req_object", test_corba_session_string, pagesize=50)
        table._get_row(2)
        self.corba_mock.VerifyAll()

    @raises(CORBA.BAD_PARAM)
    @with_setup(Initializer.setup)
    def test__get_row_out_of_index(self):
        """ _get_row raises IndexError when index is out of range. """
        self.init_itertable(self.pagetable_mock, numPages=1, numPageRows=1)

        self.pagetable_mock.getRow(-1).AndRaise(
            CORBA.BAD_PARAM(omniORB.BAD_PARAM_PythonValueOutOfRange, 
                            CORBA.COMPLETED_NO))
        self.pagetable_mock.getRowId(-2).AndReturn(1)

        self.corba_mock.ReplayAll()
        table = IterTable("test_req_object", test_corba_session_string, pagesize=50)
        table._get_row(-1)
        self.corba_mock.VerifyAll()


    @raises(CORBA.BAD_PARAM)
    @with_setup(Initializer.setup)
    def test__get_row_invalid_argument(self):
        """ _get_row raises ValueError when index is not an integer. """
        self.init_itertable(self.pagetable_mock, numPages=1, numPageRows=1)

        self.pagetable_mock.getRow("intentional error - this should be an integer").\
            AndRaise(CORBA.BAD_PARAM(omniORB.BAD_PARAM_WrongPythonType,
                     CORBA.COMPLETED_NO))
        self.pagetable_mock.getRowId(2).AndReturn(1)

        self.corba_mock.ReplayAll()
        table = IterTable("test_req_object", test_corba_session_string, pagesize=50)
        table._get_row("intentional error - this should be an integer")
        self.corba_mock.VerifyAll()


class TestGetRowDict(Initializer):
    def __init__(self):
        Initializer.__init__(self)

    @with_setup(Initializer.setup)
    def test_get_rows_dict(self):
        """ get_rows_dict returns correct row. """
        self.init_itertable(self.pagetable_mock, columnDesc=["c1", "c2"], start=0, pageSize=1, numPages=1, numPageRows=1)

        self.pagetable_mock.getRow(1).AndReturn(
            [CORBA.Any(CORBA.TC_string, 'test value'), 
             CORBA.Any(CORBA.TC_string, 'test value 2')])
        self.pagetable_mock.getRowId(1).AndReturn(1)

        self.corba_mock.ReplayAll()
        table = IterTable("test_req_object", test_corba_session_string, pagesize=50)
        rows = table.get_rows_dict(start=1)

        assert len(rows) == 1
        assert len(rows[0]) == 3
        assert rows[0]['Id'] == u'1'
        assert rows[0]["c1"] == u'test value'
        assert rows[0]["c2"] == u'test value 2'

        self.corba_mock.VerifyAll()

    @with_setup(Initializer.setup)
    def test_get_rows_dict_multiple_rows(self):
        """ get_row_dict returns multiple rows correctly. """
        self.init_itertable(self.pagetable_mock, columnDesc=["c1", "c2"], 
                            start=0, pageSize=1, numPages=1, numPageRows=1)

        self.pagetable_mock._set_pageSize(10)
        self.itertable_update(self.pagetable_mock)
        for i in range(5, 15):
            self.pagetable_mock.getRow(i).AndReturn(
                [CORBA.Any(CORBA.TC_string, 'test value'), 
                 CORBA.Any(CORBA.TC_string, 'test value 2')])
            self.pagetable_mock.getRowId(i).AndReturn(i)

        self.corba_mock.ReplayAll()
        table = IterTable("test_req_object", test_corba_session_string, pagesize=50)
        rows = table.get_rows_dict(start=5, limit=10)


class TestGetRowId(Initializer):
    def __init__(self):
        Initializer.__init__(self)

    @with_setup(Initializer.setup)
    def test_get_row_id(self):
        """ get_row_id returns correct id when index is OK. """
        self.init_itertable(self.pagetable_mock, columnDesc=["c1", "c2"], 
                            start=0, pageSize=1, numPages=1, numPageRows=1)
        self.pagetable_mock.getRowId(1).AndReturn(1)
        self.corba_mock.ReplayAll()

        table = IterTable("test_req_object", test_corba_session_string, pagesize=50)
        id = table.get_row_id(1)

        assert id == 1
        self.corba_mock.VerifyAll()

    @raises(IndexError)
    @with_setup(Initializer.setup)
    def test_get_row_id_index_out_of_bounds(self):
        """ get_row_id returns correct id when index is OK. """
        self.init_itertable(self.pagetable_mock, columnDesc=["c1", "c2"], 
                            start=0, pageSize=1, numPages=1, numPageRows=1)
        self.pagetable_mock.getRowId(10000).AndRaise(ccReg.Table.INVALID_ROW())
        self.corba_mock.ReplayAll()

        table = IterTable("test_req_object", test_corba_session_string, pagesize=50)
        id = table.get_row_id(index=10000) # index out of bounds


    @raises(IndexError)
    @with_setup(Initializer.setup)
    def test_get_row_id_negative_index(self):
        """ get_row_id returns correct id when index is OK. """
        self.init_itertable(self.pagetable_mock, columnDesc=["c1", "c2"], 
                            start=0, pageSize=1, numPages=1, numPageRows=1)
        self.pagetable_mock.getRowId(-1).AndRaise(ccReg.Table.INVALID_ROW())
        self.corba_mock.ReplayAll()

        table = IterTable("test_req_object", test_corba_session_string, pagesize=50)
        id = table.get_row_id(index=-1) # negative index

