#
# Copyright (C) 2008-2018  CZ.NIC, z. s. p. o.
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

import logging
import os
import time

import config


def setup_log():
    # After this function is executed, we can anywhere in project run import logging; loggin.debug("debug message");
    logfilename = os.path.join(config.log_dir, 'fred-webadmin-%s.log' % time.strftime('%Y%m%d'))
    if os.path.isfile(logfilename):
        print 'KEEP LOGGING TO', logfilename
        mode = 'a'
    else:
        print 'OPENING NEW LOG', logfilename
        mode = 'w'
    logging.basicConfig(level=config.log_level,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        filename=logfilename,
                        filemode=mode)
    # log messages to standard output
    console = logging.StreamHandler()
    logging.getLogger('').addHandler(console)
