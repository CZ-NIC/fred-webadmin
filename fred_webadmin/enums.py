'''
Classes with 'constant' data used for enumerations (tables translating handles to human readable text etc)
'''
import sys

import config
from fred_webadmin.corbalazy import CorbaLazyRequestIterStructToDict
from fred_webadmin.translation import _
from fred_webadmin.webwidgets.gpyweb.gpyweb import DictLookup

if sys.version_info >= (2, 7):
    from collections import OrderedDict
else:
    from fred_webadmin.utils import OrderedDict

ContactCheckEnums = DictLookup(
    TEST_STATUS_NAMES=CorbaLazyRequestIterStructToDict('Verification', None, 'listTestStatusDefs',
                                                       ['handle', 'name'], None, config.lang[:2]),
    TEST_STATUS_DESCS=CorbaLazyRequestIterStructToDict('Verification', None, 'listTestStatusDefs',
                                                       ['handle', 'description'], None, config.lang[:2]),
    CHECK_STATUS_NAMES=CorbaLazyRequestIterStructToDict('Verification', None, 'listCheckStatusDefs',
                                                        ['handle', 'name'], None, config.lang[:2]),
    CHECK_STATUS_DESCS=CorbaLazyRequestIterStructToDict('Verification', None, 'listCheckStatusDefs',
                                                        ['handle', 'description'], None, config.lang[:2]),
    TEST_NAMES=CorbaLazyRequestIterStructToDict('Verification', None, 'listTestDefs',
                                                ['handle', 'name'], None, config.lang[:2], None),
    TEST_DESCS=CorbaLazyRequestIterStructToDict('Verification', None, 'listTestDefs',
                                                ['handle', 'description'], None, config.lang[:2], None),
    SUITE_NAMES=CorbaLazyRequestIterStructToDict('Verification', None, 'listTestSuiteDefs',
                                                 ['handle', 'name'], None, config.lang[:2]),
    SUITE_DESCS=CorbaLazyRequestIterStructToDict('Verification', None, 'listTestSuiteDefs',
                                                 ['handle', 'description'], None, config.lang[:2]),
)


# enum made as function to avoid duplicate data:
def get_status_action(test_suite_handle, current_status):
    status_action = None
    if test_suite_handle == 'automatic':
        if current_status.startswith('auto_'):
            status_action = OrderedDict((('fail:add_manual', _('Resolve as failed')),
                                         ('invalidated:', _('Invalidate')),
                                         ('ok:', _('Resolve as OK'))))
    elif test_suite_handle == 'manual':
        if current_status == 'enqueue_req':
            status_action = OrderedDict((('confirm_enqueue:', _('Confirm enqueue')),
                                         ('invalidated:', _('Invalidate')),
                                         ('ok:', _('Resolve as OK'))))
        elif current_status == 'auto_to_be_decided':
            status_action = OrderedDict((('fail_req:', _('Request failed')),
                                         ('invalidated:', _('Invalidate')),
                                         ('invalidated:add_thank_you', _('Inv. + thank letter')),
                                         ('ok:', _('Resolve as OK'))))
        elif current_status == 'fail_req':
            status_action = OrderedDict((('fail:delete_domains', _('Resolve as failed')),
                                         ('invalidated:', _('Invalidate')),
                                         ('invalidated:add_thank_you', _('Inv. + thank letter')),
                                         ('ok:', _('Resolve as OK'))))
    elif test_suite_handle == 'thank_you':
        if current_status == 'auto_to_be_decided':
            status_action = OrderedDict((('fail:add_manual', _('Resolve as failed')),
                                         ('invalidated:', _('Invalidate')),
                                         ('ok:', _('Resolve as OK'))))
    if status_action is None:
        raise RuntimeError('Unknown current_status "%s" of contact check with suite "%s".' % (current_status, test_suite_handle))
    return status_action
