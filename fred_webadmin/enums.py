'''
Classes with 'constant' data used for enumerations (tables translating handles to human readable text etc)
'''
import config
from fred_webadmin.corbalazy import CorbaLazyRequestIterStructToDict


class ContactCheckEnums(object):
    TEST_STATUS_NAMES = CorbaLazyRequestIterStructToDict('Verification', None, 'listTestStatusDefs',
                                                         ['handle', 'name'], None, config.lang[:2])
    TEST_STATUS_DESCS = CorbaLazyRequestIterStructToDict('Verification', None, 'listTestStatusDefs',
                                                         ['handle', 'description'], None, config.lang[:2])
    CHECK_STATUS_NAMES = CorbaLazyRequestIterStructToDict('Verification', None, 'listCheckStatusDefs',
                                                          ['handle', 'name'], None, config.lang[:2])
    CHECK_STATUS_DESCS = CorbaLazyRequestIterStructToDict('Verification', None, 'listCheckStatusDefs',
                                                          ['handle', 'description'], None, config.lang[:2])
    TEST_NAMES = CorbaLazyRequestIterStructToDict('Verification', None, 'listTestDefs',
                                                  ['handle', 'name'], None, config.lang[:2], None)
    TEST_DESCS = CorbaLazyRequestIterStructToDict('Verification', None, 'listTestDefs',
                                                  ['handle', 'description'], None, config.lang[:2], None)
    SUITE_NAMES = CorbaLazyRequestIterStructToDict('Verification', None, 'listTestSuiteDefs',
                                                   ['handle', 'name'], None, config.lang[:2])
    SUITE_DESCS = CorbaLazyRequestIterStructToDict('Verification', None, 'listTestSuiteDefs',
                                                   ['handle', 'description'], None, config.lang[:2])
