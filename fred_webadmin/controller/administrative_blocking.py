import types

import cherrypy

from fred_webadmin import utils
from fred_webadmin.controller import views
from fred_webadmin.corba import Registry
import fred_webadmin.corbarecoder as recoder
from fred_webadmin.mappings import f_urls
from fred_webadmin.translation import _
from fred_webadmin.webwidgets.forms.adifforms import (DomainBlockForm, DomainUnblockForm,
    DomainUnblockAndRestorePrevStateForm, DomainChangeBlockingForm, DomainBlacklistForm, DomainUnblacklistAndCreateForm)


class AdministrativeBlockingBaseView(views.ProcessFormView):
    ''' Base class for processing administrative blocking form. '''

    exception_error_messages = {
        Registry.Administrative.DOMAIN_ID_NOT_FOUND: _('Domain %s not found.'),
        Registry.Administrative.DOMAIN_ID_ALREADY_BLOCKED: _('Domain %s is already blocked.'),
        Registry.Administrative.DOMAIN_ID_NOT_BLOCKED: _('Domain %s is not blocked.'),
        Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS: _('New holder %s does not exists.'),
    }

    success_url = f_urls['domain'] + 'blocking/result/'

    corba_function_name = None
    corba_function_arguments = None  # names of arguments in the form which are passed to CORBA function

    input_props = None  # list of input properties for log request

    log_req_type = None

    objects_exceptions = None  # list of exceptions_types added to 'objects' field
    field_exceptions = None  # dict of (excepion_type: field_name)

    action_name = None  # Translated name of action used for heading and buttons

    def __init__(self, **kwargs):
        self.refs = []
        self.props = []
        self.output_props = []  # when FAIL, add exception to this
        self.log_req = None
        if self.field_exceptions is None:
            self.field_exceptions = {}

        super(AdministrativeBlockingBaseView, self).__init__(**kwargs)

    def _initialize_log_req(self, form):
        self.refs.extend([('domain', domain) for domain in form.cleaned_data['objects']])
        for prop_name in self.input_props:
            prop_value = form.cleaned_data[prop_name]
            if isinstance(prop_value, types.ListType):
                self.props.extend([(prop_name, prop_item_value)
                                   for prop_item_value in form.cleaned_data[prop_name]])
            else:
                self.props.append((prop_name, prop_value))
        self.log_req = utils.create_log_request(self.log_req_type, properties=self.props, references=self.refs)

    def _get_corba_function_arguments(self, form):
        corba_arguments = [recoder.u2c(form.cleaned_data[field_name]) for field_name in self.corba_function_arguments]
        corba_arguments.append(self.log_req.request_id)
        return corba_arguments

    def get_context_data(self, **kwargs):
        kwargs['heading'] = self.action_name
        return super(AdministrativeBlockingBaseView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        self._initialize_log_req(form)
        try:
            return_value = getattr(cherrypy.session['Blocking'], self.corba_function_name)(
                *self._get_corba_function_arguments(form)
            )
            self.log_req.result = 'Success'
            cherrypy.session['blocking_result'] = {
                'blocking_action': form.cleaned_data['blocking_action'],
                'blocked_objects': form.cleaned_data['objects'],
                'return_value': return_value,
            }
            del cherrypy.session['pre_blocking_form_data']
            raise cherrypy.HTTPRedirect(self.get_success_url())
        except self.objects_exceptions, e:
            self.log_req.result = 'Fail'
            self.output_props.append(('error', type(e).__name__))
            self.output_props.extend([('error_subject_id', subject) for subject in e.what])
            form.fields['objects'].add_objects_errors(self.exception_error_messages[type(e)], e.what)
        except tuple(self.field_exceptions.keys()), e:
            self.log_req.result = 'Fail'
            self.output_props.append(('error', type(e).__name__))
            self.output_props.append(('error_subject_handle', e.what))  # pylint: disable=E1101
            exc_type = type(e)
            form.add_error(self.field_exceptions[exc_type],
                           self.exception_error_messages[exc_type] % e.what)  # pylint: disable=E1101
        finally:
            self.log_req.close(properties=self.output_props)

        return self.get_context_data(form=form)


class ProcessBlockView(AdministrativeBlockingBaseView):
    form_class = DomainBlockForm
    corba_function_name = 'blockDomainsId'
    corba_function_arguments = ['objects', 'blocking_status_list', 'owner_block_mode', 'reason']

    log_req_type = 'DomainsBlock'
    input_props = ['blocking_status_list', 'owner_block_mode', 'reason']

    objects_exceptions = (Registry.Administrative.DOMAIN_ID_NOT_FOUND,
                          Registry.Administrative.DOMAIN_ID_ALREADY_BLOCKED)

    action_name = _('Block')


class ProcessUpdateBlockingView(AdministrativeBlockingBaseView):
    form_class = DomainChangeBlockingForm
    corba_function_name = 'updateBlockDomainsId'
    corba_function_arguments = ['objects', 'blocking_status_list', 'reason']

    log_req_type = 'DomainsBlockUpdate'
    input_props = ['blocking_status_list', 'reason']

    objects_exceptions = (Registry.Administrative.DOMAIN_ID_NOT_FOUND,
                          Registry.Administrative.DOMAIN_ID_NOT_BLOCKED)

    action_name = _('Change blocking')


class ProcessUnblockView(AdministrativeBlockingBaseView):
    form_class = DomainUnblockForm
    corba_function_name = 'unblockDomainsId'
    corba_function_arguments = ['objects', 'new_holder', 'remove_admin_contacts', 'reason']

    log_req_type = 'DomainsUnblock'
    input_props = ['new_holder', 'remove_admin_contacts', 'reason']

    objects_exceptions = (Registry.Administrative.DOMAIN_ID_NOT_FOUND,
                          Registry.Administrative.DOMAIN_ID_NOT_BLOCKED)
    field_exceptions = {Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS: 'new_holder'}

    action_name = _('Unblock')

    def _initialize_log_req(self, form):
        super(ProcessUnblockView, self)._initialize_log_req(form)
        self.props.append(('restore_prev_state', False))


class ProcessUnblockAndRestorePrevStateView(AdministrativeBlockingBaseView):
    form_class = DomainUnblockAndRestorePrevStateForm
    corba_function_name = 'restorePreAdministrativeBlockStatesId'
    corba_function_arguments = ['objects', 'new_holder', 'reason']

    log_req_type = 'DomainsUnblock'
    input_props = ['new_holder', 'reason']

    objects_exceptions = (Registry.Administrative.DOMAIN_ID_NOT_FOUND,
                          Registry.Administrative.DOMAIN_ID_NOT_BLOCKED)
    field_exceptions = {Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS: 'new_holder'}

    action_name = _('Unblock and restore prev. state')

    def _initialize_log_req(self, form):
        super(ProcessUnblockAndRestorePrevStateView, self)._initialize_log_req(form)
        self.props.append(('restore_prev_state', True))


class ProcessBlacklistView(AdministrativeBlockingBaseView):
    form_class = DomainBlacklistForm
    corba_function_name = 'blacklistDomainsId'
    corba_function_arguments = ['objects', 'with_delete']

    log_req_type = 'DomainsBlacklist'
    input_props = ['with_delete', 'reason']

    objects_exceptions = Registry.Administrative.DOMAIN_ID_NOT_FOUND
    field_exceptions = {Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS: 'new_holder'}

    action_name = _('Blacklist')

    def _get_corba_function_arguments(self, form):
        result = super(ProcessBlacklistView, self)._get_corba_function_arguments(form)
        result.insert(1, None)  # second argument blacklist to date not yet in the form
        return result
