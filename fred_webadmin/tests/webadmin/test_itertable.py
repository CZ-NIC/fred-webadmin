#
# Copyright (C) 2009-2018  CZ.NIC, z. s. p. o.
#
# This file is part of FRED.
#
# FRED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FRED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FRED.  If not, see <https://www.gnu.org/licenses/>.

import cherrypy
from omniORB import CORBA
import omniORB

from mock import MagicMock, Mock, call
from nose.tools import assert_equal, assert_is_not_none, raises  # @UnresolvedImport
from fred_webadmin.corba import Registry

import fred_webadmin.itertable
from fred_webadmin.itertable import IterTable, fileGenerator

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
        # Create admin mock and add it to cherrypy.session
        self.admin_mock = Mock()
        cherrypy.session = {}
        cherrypy.session['Admin'] = self.admin_mock
        self.session_mock = Mock(name='session mock')
        self.admin_mock.getSession.return_value = self.session_mock
        self.pagetable_mock = Mock(name='pagetable mock')

        # Monkey patch the mapping.
        self.monkey_patch(fred_webadmin.itertable, 'f_name_enum',
            monkey_patched_f_name_enum)
        self.monkey_patch(fred_webadmin.itertable, 'f_enum_name',
            monkey_patched_f_enum_name)
        self.monkey_patch(fred_webadmin.itertable, 'f_urls',
            monkey_patched_f_urls)

    def init_itertable(self, columnDesc=None, page=1,
                       pageSize=5, timeout=10000, max_row_limit=1000, start=1, numRows=50,
                       numPageRows=5, rowsOverLimit=False):
        """ Utility method to prevent boilerplate code.
            Provides methods that are called by Itertable.__init__.
        """
        if columnDesc is None:
            columnDesc = ["col1", "col2"]
        self.session_mock.getPageTable.side_effect = lambda ft_type: \
            self.pagetable_mock if ft_type == test_type_corba_enum else None
        self.pagetable_mock.getColumnHeaders.return_value = \
            [Registry.Table.ColumnDesc(desc, Registry.Table.CT_OTHER) for
             desc in columnDesc]
        self.itertable_update(page, pageSize, start, numRows, numPageRows, rowsOverLimit)

    def itertable_update(self, page=1, pageSize=5, start=1,
                         numRows=50, numPageRows=5, rowsOverLimit=False):
        """ Utility method to prevent boilerplate code.
            Simulates IterTable._update method. """
        self.pagetable_mock._get_page.return_value = page
        self.pagetable_mock._get_pageSize.return_value = pageSize
        self.pagetable_mock._get_start.return_value = start
        self.pagetable_mock._get_numRows.return_value = numRows
        self.pagetable_mock.numRowsOverLimit.return_value = rowsOverLimit
        self.pagetable_mock._get_numPages.return_value = numRows / pageSize
        self.pagetable_mock._get_numPageRows.return_value = numPageRows


class TestItertable(Initializer):
    def test_init(self):
        """ IterTable initializes correctly. """
        self.init_itertable(pageSize=50)

        table = IterTable("test_req_object", test_corba_session_string, pagesize=50)

        assert_is_not_none(table)
        expected_calls = [call._set_pageSize(50),
             call.setTimeout(10000),
             call.setLimit(1000),
             call.getColumnHeaders(),
             call._get_page(),
             call._get_pageSize(),
             call._get_start(),
             call._get_numRows(),
             call.numRowsOverLimit(),
             call._get_numPages(),
             call._get_numPageRows()
        ]

        self.pagetable_mock.assert_has_calls(expected_calls, any_order=True)

    @raises(ValueError)
    def test_init_unknown_request_object(self):
        """ IterTable throws KeyError when request_object is not known. """
        self.init_itertable()
        IterTable("test_invalid_req_object", test_corba_session_string, pagesize=50)


class Test_getRow(Initializer):
    def test__get_row(self):
        """_get_row returns row correctly. """
        self.init_itertable(pageSize=50)

        self.pagetable_mock.getRow.side_effect = lambda row_num: \
            [CORBA.Any(CORBA.TC_string, 'test value')] if row_num == 2 else None
        self.pagetable_mock.getRowId.side_effect = lambda row_num: \
            12 if row_num == 2 else None
        table = IterTable('test_req_object', test_corba_session_string, pagesize=50)
        row = table._get_row(2)

        assert_equal(len(row), 2)

        assert_equal(row[0]['url'], "www.test.foo/baz/detail/?id=12")
        assert_equal(row[0]['index'], 0)
        assert_is_not_none(row[0]['icon'])

        assert_equal(row[1]['index'], 1)
        assert_equal(row[1]['value'], 'test value')

        expected_calls = [call.getRow(2),
                          call.getRowId(2)]
        self.pagetable_mock.assert_has_calls(expected_calls, any_order=True)

    @raises(IndexError)
    def test__get_row_out_of_index(self):
        """ _get_row raises IndexError when index is out of range. """
        self.init_itertable(numPageRows=1, pageSize=50)

        self.pagetable_mock.getRow.side_effect = Registry.Table.INVALID_ROW

        table = IterTable('test_req_object', test_corba_session_string, pagesize=50)
        table._get_row(2)

    @raises(CORBA.BAD_PARAM)
    def test__get_row_invalid_argument(self):
        """ _get_row fails when index is not an integer. """
        self.init_itertable(numPageRows=1, pageSize=50)

        # simulate that getRow was called with bad argument like string instead int:
        self.pagetable_mock.getRow.side_effect = \
            CORBA.BAD_PARAM(omniORB.BAD_PARAM_WrongPythonType, CORBA.COMPLETED_NO)

        table = IterTable("test_req_object", test_corba_session_string, pagesize=50)
        table._get_row("intentional error - this should be an integer")


class TestGetRowDict(Initializer):
    def __init__(self):
        Initializer.__init__(self)

    def test_get_rows_dict(self):
        """ get_rows_dict returns correct rows when no arguments are given. """
        self.init_itertable(
            columnDesc=["c1", "c2"], page=1, pageSize=2,
            start=5, numRows=10, numPageRows=2)
        self.pagetable_mock.getRow.side_effect = lambda row_num: \
            {5: [CORBA.Any(CORBA.TC_string, 'test value 1.1'),
                 CORBA.Any(CORBA.TC_string, 'test value 1.2')],
             6: [CORBA.Any(CORBA.TC_string, 'test value 2.1'),
                 CORBA.Any(CORBA.TC_string, 'test value 2.2')],
            }[row_num]
        self.pagetable_mock.getRowId.side_effect = lambda row_num: row_num

        table = IterTable('test_req_object', test_corba_session_string, pagesize=2)
        rows = table.get_rows_dict()

        assert_equal(len(rows), 2)

        assert_equal(len(rows[0]), 3)
        assert_equal(rows[0].get(u'Id'), u'5')
        assert_equal(rows[0].get(u'c1'), u'test value 1.1')
        assert_equal(rows[0].get(u'c2'), u'test value 1.2')

        assert_equal(len(rows[1]), 3)
        assert_equal(rows[1].get(u'Id'), u'6')
        assert_equal(rows[1].get(u'c1'), u'test value 2.1')
        assert_equal(rows[1].get(u'c2'), u'test value 2.2')

    def test_get_rows_dict_multiple_rows(self):
        """ get_rows_dict returns multiple rows correctly. """
        self.init_itertable(columnDesc=["c1", "c2"],
                            start=0, numPageRows=1, numRows=20, pageSize=10)

        self.pagetable_mock.getRow.side_effect = lambda row_num: \
                [CORBA.Any(CORBA.TC_string, 'test value %i.1' % row_num),
                 CORBA.Any(CORBA.TC_string, 'test value %i.2' % row_num)]
        self.pagetable_mock.getRowId.side_effect = lambda row_num: row_num

        table = IterTable('test_req_object', test_corba_session_string, pagesize=10)
        rows = table.get_rows_dict(start=5, limit=11)

        assert_equal(len(rows), 11)
        assert_equal(len(rows[6]), 3)
        assert_equal(rows[6].get(u'Id'), u'11')
        assert_equal(rows[6].get(u'c1'), u'test value 11.1')
        assert_equal(rows[6].get(u'c2'), u'test value 11.2')

    @raises(IndexError)
    def test_get_rows_dict_multiple_rows_index_error(self):
        """ get_row_dict raises IndexError when wrong index used. """
        self.init_itertable(columnDesc=["c1", "c2"],
                            start=0, numPageRows=1, numRows=20, pageSize=10)
        self.itertable_update()
        self.pagetable_mock.getRow.side_effect = Registry.Table.INVALID_ROW

        table = IterTable('test_req_object', test_corba_session_string, pagesize=10)
        table.get_rows_dict(start=21, limit=100)


class TestGetRowId(Initializer):
    def __init__(self):
        Initializer.__init__(self)

    def test_get_row_id(self):
        """ get_row_id returns correct id when index is OK. """
        self.init_itertable(columnDesc=["c1", "c2"],
                            start=0, numPageRows=1, numRows=20, pageSize=5)
        self.pagetable_mock.getRowId.return_value = 1

        table = IterTable('test_req_object', test_corba_session_string, pagesize=5)
        row_id = table.get_row_id(1)

        assert_equal(row_id, 1)

    @raises(IndexError)
    def test_get_row_id_index_out_of_bounds(self):
        """ get_row_id raises IndexError when index is too big. """
        self.init_itertable()
        self.pagetable_mock.getRowId.side_effect = Registry.Table.INVALID_ROW

        table = IterTable('test_req_object', test_corba_session_string, pagesize=50)
        table.get_row_id(index=10000)  # index out of bounds


class TestIteration(Initializer):
    def __init__(self):
        Initializer.__init__(self)

    def test_next(self):
        """ IterTable works as an iterator (`for row in itertable` expression
            works).
        """
        self.init_itertable(columnDesc=["c1", "c2"],
                            start=0, numPageRows=10, numRows=20, pageSize=5)
        self.pagetable_mock.getRow.side_effect = lambda row_num: \
                [CORBA.Any(CORBA.TC_string, 'test value %i.1' % row_num),
                 CORBA.Any(CORBA.TC_string, 'test value %i.2' % row_num)]
        self.pagetable_mock.getRowId.side_effect = lambda row_num: row_num

        table = IterTable('test_req_object', test_corba_session_string, pagesize=5)
        for i, row in enumerate(table):
            assert_is_not_none(row)
            assert_equal(len(row), 3)
            if i == 0:
                assert_equal(row[0].get(u'value'), "")
            else:
                assert_equal(row[0].get(u'value'), str(i))


class TestFileGenerator(object):
    def setUp(self):
        rows = [
            [{'value': '1'}, {'value': '2'}, {'value': '3'}, {'value': '4'}],
            [{'value': '4'}, {'value': '3'}, {'value': '2'}, {'value': '1'}],
        ]
        self.source_mock = MagicMock()
        self.source_mock.__getitem__.side_effect = rows
        self.source_mock.rawheader = ['First', 'Second', 'Third', 'Fourth']
        self.source_mock.num_rows = 2

    def test_without_columns(self):
        expected = ('First,Second,Third,Fourth\r\n'
                    '1,2,3,4\r\n'
                    '4,3,2,1\r\n')
        result = ''.join(fileGenerator(self.source_mock))
        assert_equal(result, expected)

    def test_with_columns(self):
        columns = ['Third', 'Additional', 'First']
        expected = ('Third,Additional,First\r\n'
                    '3,,1\r\n'
                    '2,,4\r\n')
        result = ''.join(fileGenerator(self.source_mock, columns))
        assert_equal(result, expected)
