import mox
import cherrypy
from omniORB import CORBA
import omniORB

from nose.tools import with_setup, raises
from fred_webadmin.corba import Registry, ccReg

import fred_webadmin.itertable
from fred_webadmin.itertable import IterTable

test_type_corba_enum = 42

""" We have decided to use monkey patching to avoid the necessity of
    refactoring IterTable to accept webadmin -> corba mapping as an
    argument (old codebase with no tests, ugh...). """
monkey_patched_f_name_enum = {}
monkey_patched_f_name_enum["test_req_object"] = test_type_corba_enum

monkey_patched_f_enum_name = {}
monkey_patched_f_enum_name[test_type_corba_enum] = "test_req_object"

monkey_patched_f_urls = {}
monkey_patched_f_urls["test_req_object"] = "www.test.foo/baz/"

# Fake session string for Corba session
test_corba_session_string = "test_ses_key"


class Initializer(object):
    """
        Utility class for preventing boilerplate code.
        TODO(tomas): Probably may not be be a class at all.
    """

    def __init__(self, *args, **kwargs):
        self.corba_mock = None
        self.admin_mock = None
        self.session_mock = None
        self.pagetable_mock = None
        self._on_teardown = []

    def monkey_patch(self, obj, attr, new_value):
        """ Taken from
            http://lackingrhoticity.blogspot.com/2008/12/
            helper-for-monkey-patching-in-tests.html

            Basically it stores the original object before monkeypatching and
            then restores it at teardown. Which is handy, because we do not
            want the object to stay monkeypatched between unit tests (if the
            test needs to do the patch, it can, but it should not change the
            environment for the other tests.
        """
        old_value = getattr(obj, attr)
        def tear_down():
            setattr(obj, attr, old_value)
        self._on_teardown.append(tear_down)
        setattr(obj, attr, new_value)

    def tearDown(self):
        """ Taken from
            http://lackingrhoticity.blogspot.com/2008/12/
            helper-for-monkey-patching-in-tests.html"""
        for func in reversed(self._on_teardown):
            func()

    def setUp(self):
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

        # Monkey patch the mapping.
        self.monkey_patch(fred_webadmin.itertable, "f_name_enum",
            monkey_patched_f_name_enum)
        self.monkey_patch(fred_webadmin.itertable, "f_enum_name",
            monkey_patched_f_enum_name)
        self.monkey_patch(fred_webadmin.itertable, "f_urls",
            monkey_patched_f_urls)

    def init_itertable(self, pagetable_mock, columnDesc=None, page=1,
                       pageSize=5, timeout=10000, max_row_limit=1000, start=1, numRows=50,
                       numPageRows=5, rowsOverLimit=False):
        """ Utility method to prevent boilerplate code.
            Provides methods that are called by Itertable.__init__.
        """
        if columnDesc is None:
            columnDesc = ["col1", "col2"]
        self.session_mock.getPageTable(test_type_corba_enum).AndReturn(
            self.pagetable_mock)
        pagetable_mock.getColumnHeaders().InAnyOrder("initpt").AndReturn(
            [Registry.Table.ColumnDesc(desc, Registry.Table.CT_OTHER) for
             desc in columnDesc])
        pagetable_mock._set_pageSize(pageSize).InAnyOrder("initpt")
        pagetable_mock.setLimit(max_row_limit).InAnyOrder("initpt")
        pagetable_mock.setTimeout(timeout).InAnyOrder("initpt")
        self.itertable_update(
            pagetable_mock, page, pageSize, start, numRows,
            numPageRows, rowsOverLimit)

    def itertable_update(self, pagetable_mock, page=1, pageSize=5, start=1,
                     numRows=50, numPageRows=5, rowsOverLimit=False):
        """ Utility method to prevent boilerplate code.
            Simulates IterTable._update method. """
        pagetable_mock._get_page().InAnyOrder("updatept").AndReturn(page)
        pagetable_mock._get_pageSize().InAnyOrder("updatept").AndReturn(
            pageSize)
        pagetable_mock._get_start().InAnyOrder("updatept").AndReturn(start)
        pagetable_mock._get_numRows().InAnyOrder("updatept").AndReturn(numRows)
        pagetable_mock.numRowsOverLimit().InAnyOrder(
            "updatept").AndReturn(rowsOverLimit)
        pagetable_mock._get_numPages().InAnyOrder("updatept").AndReturn(
            numRows / pageSize)
        pagetable_mock._get_numPageRows().InAnyOrder(
            "updatept").AndReturn(numPageRows)


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

    def test_init(self):
        """ IterTable initializes correctly. """
        self.init_itertable(self.pagetable_mock, pageSize=50)

        self.corba_mock.ReplayAll()

        table = IterTable("test_req_object", test_corba_session_string, pagesize=50)

        assert table is not None
        self.corba_mock.VerifyAll()

    @raises(ValueError)
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

    def test__get_row(self):
        """_get_row returns row correctly. """
        self.init_itertable(self.pagetable_mock, pageSize=50)
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
    def test__get_row_out_of_index(self):
        """ _get_row raises IndexError when index is out of range. """
        self.init_itertable(self.pagetable_mock, numPageRows=1, pageSize=50)

        self.pagetable_mock.getRow(2).AndRaise(
            CORBA.BAD_PARAM(omniORB.BAD_PARAM_PythonValueOutOfRange,
                            CORBA.COMPLETED_NO))
        self.pagetable_mock.getRowId(2).AndReturn(1)

        self.corba_mock.ReplayAll()
        table = IterTable("test_req_object", test_corba_session_string, pagesize=50)
        table._get_row(2)
        self.corba_mock.VerifyAll()

    @raises(CORBA.BAD_PARAM)
    def test__get_row_out_of_index(self):
        """ _get_row raises IndexError when index is out of range. """
        self.init_itertable(self.pagetable_mock, numPageRows=1, pageSize=50)

        self.pagetable_mock.getRow(-1).AndRaise(
            CORBA.BAD_PARAM(omniORB.BAD_PARAM_PythonValueOutOfRange,
                            CORBA.COMPLETED_NO))
        self.pagetable_mock.getRowId(-2).AndReturn(1)

        self.corba_mock.ReplayAll()
        table = IterTable("test_req_object", test_corba_session_string, pagesize=50)
        table._get_row(-1)
        self.corba_mock.VerifyAll()


    @raises(CORBA.BAD_PARAM)
    def test__get_row_invalid_argument(self):
        """ _get_row raises ValueError when index is not an integer. """
        self.init_itertable(self.pagetable_mock, numPageRows=1, pageSize=50)

        self.pagetable_mock.getRow(
            "intentional error - this should be an integer").AndRaise(
            CORBA.BAD_PARAM(
                omniORB.BAD_PARAM_WrongPythonType, CORBA.COMPLETED_NO))
        self.pagetable_mock.getRowId(2).AndReturn(1)

        self.corba_mock.ReplayAll()
        table = IterTable(
            "test_req_object", test_corba_session_string, pagesize=50)
        table._get_row("intentional error - this should be an integer")
        self.corba_mock.VerifyAll()


class TestGetRowDict(Initializer):
    def __init__(self):
        Initializer.__init__(self)

    def test_get_rows_dict(self):
        """ get_rows_dict returns correct rows when no arguments are given. """
        self.init_itertable(
            self.pagetable_mock, columnDesc=["c1", "c2"], page=1, pageSize=2,
            start=5, numRows=10, numPageRows=2)
        self.pagetable_mock.getRow(5).AndReturn(
            [CORBA.Any(CORBA.TC_string, 'test value 1.1'),
             CORBA.Any(CORBA.TC_string, 'test value 1.2')])
        self.pagetable_mock.getRowId(5).AndReturn(5)
        self.pagetable_mock.getRow(6).AndReturn(
            [CORBA.Any(CORBA.TC_string, 'test value 2.1'),
             CORBA.Any(CORBA.TC_string, 'test value 2.2')])
        self.pagetable_mock.getRowId(6).AndReturn(6)
        self.corba_mock.ReplayAll()

        table = IterTable(
            "test_req_object", test_corba_session_string, pagesize=2)
        rows = table.get_rows_dict()

        assert len(rows) == 2

        assert len(rows[0]) == 3
        assert rows[0].get(u'Id') == u'5'
        assert rows[0].get(u'c1') == u'test value 1.1'
        assert rows[0].get(u'c2') == u'test value 1.2'

        assert len(rows[1]) == 3
        assert rows[1].get(u'Id') == u'6'
        assert rows[1].get(u'c1') == u'test value 2.1'
        assert rows[1].get(u'c2') == u'test value 2.2'

        self.corba_mock.VerifyAll()

    def test_get_rows_dict_multiple_rows(self):
        """ get_rows_dict returns multiple rows correctly. """
        self.init_itertable(self.pagetable_mock, columnDesc=["c1", "c2"],
                            start=0, numPageRows=1, numRows=20, pageSize=10)
        self.pagetable_mock._set_pageSize(11)
        self.itertable_update(self.pagetable_mock)
        for i in range(5, 16):
            self.pagetable_mock.getRow(i).AndReturn(
                [CORBA.Any(CORBA.TC_string, 'test value %i.1' % i),
                 CORBA.Any(CORBA.TC_string, 'test value %i.2' % i)])
            self.pagetable_mock.getRowId(i).AndReturn(i)
        self.corba_mock.ReplayAll()

        table = IterTable(
            "test_req_object", test_corba_session_string, pagesize=10)
        rows = table.get_rows_dict(start=5, limit=11)

        assert len(rows) == 11
        assert len(rows[6]) == 3
        assert rows[6].get(u'Id') == u'11'
        assert rows[6].get(u'c1') == u'test value 11.1'
        assert rows[6].get(u'c2') == u'test value 11.2'

    @raises(IndexError)
    def test_get_rows_dict_multiple_rows(self):
        """ get_row_dict returns multiple rows correctly. """
        self.init_itertable(self.pagetable_mock, columnDesc=["c1", "c2"],
                            start=0, numPageRows=1, numRows=20, pageSize=10)
        self.pagetable_mock._set_pageSize(100)
        self.itertable_update(self.pagetable_mock)
        self.pagetable_mock.getRow(21).AndRaise(Registry.Table.INVALID_ROW)
        self.corba_mock.ReplayAll()

        table = IterTable(
            "test_req_object", test_corba_session_string, pagesize=10)
        rows = table.get_rows_dict(start=21, limit=100)


class TestGetRowId(Initializer):
    def __init__(self):
        Initializer.__init__(self)

    def test_get_row_id(self):
        """ get_row_id returns correct id when index is OK. """
        self.init_itertable(self.pagetable_mock, columnDesc=["c1", "c2"],
                            start=0, numPageRows=1, numRows=20, pageSize=5)
        self.pagetable_mock.getRowId(1).AndReturn(1)
        self.corba_mock.ReplayAll()

        table = IterTable(
            "test_req_object", test_corba_session_string, pagesize=5)
        id = table.get_row_id(1)

        assert id == 1
        self.corba_mock.VerifyAll()

    @raises(IndexError)
    def test_get_row_id_index_out_of_bounds(self):
        """ get_row_id raises IndexError when index is too big. """
        self.init_itertable(self.pagetable_mock, columnDesc=["c1", "c2"],
                            start=0, numPageRows=1, pageSize=50)
        self.pagetable_mock.getRowId(10000).AndRaise(Registry.Table.INVALID_ROW())
        self.corba_mock.ReplayAll()

        table = IterTable("test_req_object", test_corba_session_string, pagesize=50)
        id = table.get_row_id(index=10000) # index out of bounds


    @raises(IndexError)
    def test_get_row_id_negative_index(self):
        """ get_row_id raises IndexError when index negative. """
        self.init_itertable(self.pagetable_mock, columnDesc=["c1", "c2"],
                            start=0, numPageRows=1, pageSize=50)
        self.pagetable_mock.getRowId(-1).AndRaise(Registry.Table.INVALID_ROW())
        self.corba_mock.ReplayAll()

        table = IterTable("test_req_object", test_corba_session_string, pagesize=50)
        id = table.get_row_id(index= -1) # negative index


class TestIteration(Initializer):
    def __init__(self):
        Initializer.__init__(self)

    def test_next(self):
        """ IterTable works as an iterator (`for row in itertable` expression
            works).
        """
        self.init_itertable(self.pagetable_mock, columnDesc=["c1", "c2"],
                            start=0, numPageRows=10, numRows=20, pageSize=5)
        for i in range(0, 10):
            self.pagetable_mock.getRow(i).AndReturn(
                [CORBA.Any(CORBA.TC_string, 'test value %i.1' % i),
                CORBA.Any(CORBA.TC_string, 'test value %i.2' % i)])
            self.pagetable_mock.getRowId(i).AndReturn(i)
        self.corba_mock.ReplayAll()

        table = IterTable("test_req_object", test_corba_session_string, pagesize=5)
        for i, row in enumerate(table):
            assert row is not None
            assert len(row) == 3
            if i == 0:
                assert row[0].get(u'value') == ""
            else:
                assert row[0].get(u'value') == str(i)

        self.corba_mock.VerifyAll()
