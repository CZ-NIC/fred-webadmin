from logging import debug, error
import sys

import cherrypy

from fred_webadmin import config
from fred_webadmin import exposed
from fred_webadmin import utils
from fred_webadmin.customview import CustomView
from fred_webadmin.mappings import (f_name_actiondetailname, f_name_req_object_type)
from fred_webadmin.menunode import menu_tree
from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget, DictLookup
from fred_webadmin.webwidgets.menu import MenuHoriz
# This must all be imported because of the way templates are dealt with.
from fred_webadmin.webwidgets.templates.pages import (
    BaseSite, BaseSiteMenu, LoginPage, DisconnectedPage, NotFound404Page,
    AllFiltersPage, FilterPage, ErrorPage, DigPage, SetInZoneStatusPage,
    DomainDetail, ContactDetail, NSSetDetail, KeySetDetail, RegistrarDetail,
    PublicRequestDetail, MailDetail, InvoiceDetail, LoggerDetail,
    RegistrarEdit, BankStatementPairingEdit, BankStatementDetail,
    BankStatementDetailWithPaymentPairing, GroupEditorPage, MessageDetail,
    DomainBlocking, DomainBlockingResult
)


class Page(object):
    """ Index page, similiar to index.php, index.html and so on.
    """
    __metaclass__ = exposed.AdifPageMetaClass

    def default(self, *params, **kwd):
        """catch-all for any non-defined method"""
        return '%s,%s,%s' % (self.__class__, params, kwd)


class AdifPage(Page):
    def __init__(self):
        Page.__init__(self)
        self.classname = self.__class__.__name__.lower()
        self.menu_tree = menu_tree

    def _template(self, action=''):
        if action == 'base':
            return BaseSiteMenu
        if action == 'login':
            return LoginPage
        elif action in ('filter', 'list', 'blocking'):
            return FilterPage
        elif action == 'allfilters':
            return AllFiltersPage
        elif action == 'disconnected':
            return DisconnectedPage
        elif action == '404_not_found':
            cherrypy.response.status = 404
            return NotFound404Page
        elif action == 'error':
            return ErrorPage
        elif action == 'dig':
            return DigPage
        elif action == 'pairstatements':
            return BankStatementPairingEdit
        elif action == 'setinzonestatus':
            return SetInZoneStatusPage
        else:
            # returns ClassName + Action (e.g. DomainDetail) class from
            # module of this class, if there is no such, then it returns
            # BaseSiteMenu:
            template_name = self.__class__.__name__ + action.capitalize()
            debug('Trying to get template:' + template_name)
            template = getattr(
                sys.modules[__name__], template_name, None)
            if template is None:
                error("TEMPLATE %s IN MODULE %s NOT FOUND, USING DEFAULT: "
                      "BaseSiteMenu" % (template_name,
                      sys.modules[__name__]))
                template = BaseSiteMenu
            else:
                debug('...OK, template %s taken' % template_name)
            if not issubclass(template, WebWidget):
                raise RuntimeError("%s is not derived from WebWidget - it "
                                   "cannot be template!" % repr(template))
            return template

    def _get_menu(self, action):
        return MenuHoriz(
            self.menu_tree, self._get_menu_handle(action),
            cherrypy.session['user'])

    def _get_menu_handle(self, action):
        if self.classname in ('registrar'):
            if action in ('allfilters', 'filter'):
                return self.classname + 'filter'
            elif action in ('create', 'list'):
                return self.classname + action
        if self.classname == 'file':
            return 'summary'

        return self.classname

    def _get_selected_menu_body_id(self, action):
        handle = self._get_menu_handle(action)
        menu_node = self.menu_tree.get_menu_by_handle(handle)
        if menu_node is None:
            return ''
        return menu_node.body_id

    def _render(self, action='', ctx=None):
        context = DictLookup()
        context.approot = '/'
        context.classname = self.classname
        context.classroot = "%s%s/" % (context.approot, context.classname)
        context.corba_server = cherrypy.session.get('corba_server_name')
        context.request = cherrypy.request
        context.history = cherrypy.session.get('history', False)

        user = cherrypy.session.get('user', None)
        if user:
            context.user = user
            # None for Login page that has no menu.
            context.menu = self._get_menu(action) or None
            context.body_id = self._get_selected_menu_body_id(action)

        if ctx:
            context.update(ctx)

        temp_class = self._template(action)(context)
        result = temp_class.render()

        return result

    def default(self, *params, **kwd):
        if config.debug:
            return '%s<br/>%s' % (str(kwd), str(params))
        else:
            return self._render('404_not_found')

    def _remove_session_data(self):
        cherrypy.session['user'] = None
        cherrypy.session['corbaSession'] = None
        cherrypy.session['corbaSessionString'] = None
        cherrypy.session['corba_server_name'] = None
        cherrypy.session['logger_session_id'] = None
        cherrypy.session['Admin'] = None
        cherrypy.session['Mailer'] = None
        cherrypy.session['FileManager'] = None
        cherrypy.session['Messages'] = None
        cherrypy.session['Logger'] = None
        cherrypy.session['Blocking'] = None
        cherrypy.session['filter_forms_javascript'] = None
        cherrypy.session['filterforms'] = None

    def _create_log_req_for_object_view(self, request_type=None, properties=None, references=None, **kwd):
        '''
            To avoid code duplication - this is common for all views (like detail) which
            are taking id of an object.
            request_type - default is view detail
            It checks if ID is integer, returns errorpage if not otherwise creates new
            log request with references and object_id in properties.
            (note: object_id in properties will be obsolete when references will be everywhere)
        '''

        context = {}
        try:
            object_id = int(kwd.get('id'))
        except (TypeError, ValueError):
            context['message'] = _("Required_integer_as_parameter")
            raise CustomView(self._render('error', ctx=context))

        if request_type is None:
            request_type = f_name_actiondetailname[self.classname]

        if properties is None:
            properties = []
        if references is None:
            references = []

        properties.append(('object_id', object_id))
        object_type = f_name_req_object_type.get(self.classname)
        if object_type:
            references.append((object_type, object_id))

        log_req = utils.create_log_request(request_type, properties=properties, references=references)
        return log_req
