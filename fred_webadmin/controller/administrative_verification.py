import datetime
import json

import cherrypy

from .base import AdifPage
from fred_webadmin import config
from fred_webadmin.controller.perms import check_nperm, login_required
from fred_webadmin.corbalazy import CorbaLazyRequest, CorbaLazyRequestIterStructToDict
from fred_webadmin.corbarecoder import c2u
from fred_webadmin.customview import CustomView
from fred_webadmin.utils import create_log_request
from fred_webadmin.webwidgets.gpyweb.gpyweb import DictLookup
from fred_webadmin.webwidgets.simple_table import SimpleTable
from fred_webadmin.webwidgets.templates.pages import ContactCheckList
from fred_webadmin.mappings import f_urls
from fred_webadmin.translation import _


class ContactCheck(AdifPage):
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

    # TODO: permissions @check_nperm(['read.testsuit.automatic', 'read.testsuit.manual'])
    def index(self, *args, **kwargs):
        context = DictLookup()
        context.main = 'Welcome on the contact verification page.'
        return self._render('base', ctx=context)

    def _get_contact_checks(self, test_suit=None, contact_id=None):
        log_req = create_log_request('ContactCheckFilter')
        try:
            verif_corba = cherrypy.session['Verification']
            checks = verif_corba.getActiveChecks(test_suit)
            log_req.result = 'Success'
            return checks
        finally:
            log_req.close()

    def _table_data_generator(self, test_suit=None, contact_id=None):
        checks = self._get_contact_checks(test_suit, contact_id)

        for check in checks:
            test_finished_python = c2u(check.last_test_finished)
            if test_finished_python:
                if check.test_suite_handle == 'automatic':
                    to_resolve = test_finished_python
                elif check.test_suite_handle == 'manual':
                    last_contact_update = c2u(check.last_contact_update)
                    to_resolve = min(test_finished_python + datetime.timedelta(30),  # TODO: put into config
                                     last_contact_update)
                to_resolve = to_resolve.isoformat()
            else:
                to_resolve = ''
            row = [
                '''<a href="{0}/detail/{1}/"><img src="/img/icons/open.png" title="{3}" /></a>
                   <a href="{0}/detail/{1}/resolve/">{2}</a>'''.format(f_urls[self.classname],
                                                                       c2u(check.check_handle),
                                                                       _('Resolve'), _('Show')),
                '<a href="{}/detail/?id={}">{}</a>'.format(f_urls['contact'], c2u(check.contact_id), c2u(check.contact_handle)),
                self.SUITE_NAMES.get(c2u(check.test_suite_handle), _('!Unknown error!')),
                to_resolve,
                c2u(check.created).isoformat(),
                self.CHECK_STATUS_NAMES.get(c2u(check.current_status), _('!Unknown error!')),
            ]
            yield row

    @login_required
    def filter(self, contact_id=None):
        table_tag = SimpleTable(
                     header=[_('Action'), _('Contact'), _('Check type'), _('To resolve since'), _('Create date'), _('Status')],
                     data=None,
                     id='table_tag',
                     cssc='itertable',
                 )
        table_tag.media_files.extend(['/css/itertable.css',
                                      '/js/scw.js', '/js/scwLanguages.js',
                                      '/js/jquery.dataTables.js', '/js/contactcheck_list.js'])
        context = DictLookup({
            'heading': _('Contact checks'),
            'table_tag': table_tag,
        })
        return self._render('filter', ctx=context)

    @login_required
    def json_filter(self, **kwd):
        test_suit = kwd.get('test_suit')
        try:
            if kwd.get('contact_id'):
                contact_id = int(kwd.get('contact_id'))
            else:
                contact_id = None
        except (TypeError, ValueError):
            context = {'main': _('Requires integer as parameter (got %s).' % kwd['contact_id'])}
            raise CustomView(self._render('base', ctx=context))

        cherrypy.response.headers['Content-Type'] = 'application/json'
        data = list(self._table_data_generator(test_suit, contact_id))
        json_data = json.dumps({'aaData': data})
        return json_data

    def _template(self, action=''):
        if action == 'filter':
            return ContactCheckList
        else:
            return super(ContactCheck, self)._template(action=action)

    def _get_menu_handle(self, action):
        return 'contactcheck'
