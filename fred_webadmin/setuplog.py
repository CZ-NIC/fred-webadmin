import sys

sys.path.insert(0, '')

import logging
import os
import time

import config


def setup_log():
    # After this function is executed, we can anywhere in project run import logging; loggin.debug("debug message");
    logfilename = os.path.join(config.log_dir, 'fred-webadmin-%s.log' % time.strftime('%Y%m%d'))
    if os.path.isfile(logfilename):
        print 'KEEP LOGGING TO', logfilename
        mode='a'
    else:
        print 'OPENING NEW LOG', logfilename
        mode='w'
    logging.basicConfig(level=config.log_level,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        filename=logfilename,
                        filemode=mode)
    # display log messages to standard output
    console = logging.StreamHandler()
    logging.getLogger('').addHandler(console)
