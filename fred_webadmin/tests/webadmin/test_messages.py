#
# Copyright (C) 2014-2018  CZ.NIC, z. s. p. o.
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
from nose.tools import assert_equal

from fred_webadmin import config
from fred_webadmin.messages import info, error, debug, get_messages, DEBUG, INFO, get_level, set_level, success, warning
from fred_webadmin.tests.webadmin.base import DaphneBaseTestCase


class TestMessages(DaphneBaseTestCase):
    msg_str = 'Alleluiah'

    def setUp(self):
        self.monkey_patch(cherrypy, 'session', {})
        self.monkey_patch(config, 'messages_level', None)

    def test_message(self):
        info(self.msg_str)
        messages = get_messages()
        assert_equal(len(messages), 1)
        message = messages[0]
        assert_equal(unicode(message), self.msg_str)
        assert_equal(message.level, INFO)
        assert_equal(message.string_level, 'info')

    def test_all_levels(self):
        debug(self.msg_str)
        info(self.msg_str)
        success(self.msg_str)
        warning(self.msg_str)
        error(self.msg_str)

    def test_delete_messages(self):
        info(self.msg_str)
        error(self.msg_str)
        assert_equal(len(get_messages(delete=False)), 2)
        assert_equal(len(get_messages()), 2)
        assert_equal(len(get_messages()), 0)

    def test_miminum_recording_level(self):
        assert_equal(len(get_messages(delete=False)), 0)
        assert_equal(get_level(), INFO)  # default level is INFO
        info(self.msg_str)
        assert_equal(len(get_messages(delete=False)), 1)
        debug(self.msg_str)  # this message should not be recorded
        assert_equal(len(get_messages(delete=False)), 1)

        set_level(DEBUG)
        debug(self.msg_str)
        assert_equal(len(get_messages(delete=False)), 2)

        error(self.msg_str)  # test that also higher levels are recorded
        assert_equal(len(get_messages(delete=False)), 3)
