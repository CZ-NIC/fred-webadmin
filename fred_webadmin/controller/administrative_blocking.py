import cherrypy

from fred_webadmin.controller import views
from fred_webadmin.corba import Registry
from fred_webadmin.mappings import f_urls
from fred_webadmin.translation import _
from fred_webadmin.webwidgets.forms.adifforms import (DomainBlockForm, DomainUnblockForm,
    DomainUnblockAndRestorePrevStateForm, DomainChangeBlockingForm, DomainBlacklistAndDeleteForm)


class AdministrativeBlockingBaseView(views.ProcessFormCorbaLogView):
    ''' Base class for processing administrative blocking form. '''

    corba_backend_name = 'Blocking'

    exception_error_messages = {
        Registry.Administrative.DOMAIN_ID_NOT_FOUND: _('Domain %s not found.'),
        Registry.Administrative.DOMAIN_ID_ALREADY_BLOCKED: _('Domain %s is already blocked.'),
        Registry.Administrative.DOMAIN_ID_NOT_BLOCKED: _('Domain %s is not blocked.'),
        Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS: _('New holder {exc.what} does not exists.'),
    }

    success_url = f_urls['domain'] + 'blocking/result/'

    objects_exceptions = None  # tuple of exceptions_types added to 'objects' field

    action_name = None  # Translated name of action used for heading and buttons

    def __init__(self, **kwargs):
        super(AdministrativeBlockingBaseView, self).__init__(**kwargs)
        if self.objects_exceptions is None:
            self.objects_exceptions = ()
        else:
            for exception in self.objects_exceptions:
                self.field_exceptions[exception] = 'objects'

    def get_context_data(self, **kwargs):
        kwargs['heading'] = self.action_name
        return super(AdministrativeBlockingBaseView, self).get_context_data(**kwargs)

    def corba_call_success(self, return_value, form):
        super(AdministrativeBlockingBaseView, self).corba_call_success(return_value, form)
        cherrypy.session['blocking_result'] = {
            'blocking_action': form.cleaned_data['blocking_action'],
            'blocked_objects': form.cleaned_data['objects'],
            'return_value': return_value,
        }
        del cherrypy.session['pre_blocking_form_data']

    def corba_call_fail(self, exception, form):
        if type(exception) in self.objects_exceptions:
            self.log_req.result = 'Fail'
            self.output_props.append(('error', type(exception).__name__))
            self.output_props.extend([('error_subject_id', subject) for subject in exception.what])
            form.fields['objects'].add_objects_errors(self.exception_error_messages[type(exception)], exception.what)
        else:
            super(AdministrativeBlockingBaseView, self).corba_call_fail(exception, form)


class ProcessBlockView(AdministrativeBlockingBaseView):
    form_class = DomainBlockForm
    corba_function_name = 'blockDomainsId'
    corba_function_arguments = ['objects', 'blocking_status_list', 'owner_block_mode', 'block_to_date', 'reason']

    log_req_type = 'DomainsBlock'
    log_input_props_names = ['blocking_status_list', 'owner_block_mode', 'block_to_date', 'reason']

    objects_exceptions = (Registry.Administrative.DOMAIN_ID_NOT_FOUND,
                          Registry.Administrative.DOMAIN_ID_ALREADY_BLOCKED)

    action_name = _('Block')


class ProcessUpdateBlockingView(AdministrativeBlockingBaseView):
    form_class = DomainChangeBlockingForm
    corba_function_name = 'updateBlockDomainsId'
    corba_function_arguments = ['objects', 'blocking_status_list', 'block_to_date', 'reason']

    log_req_type = 'DomainsBlockUpdate'
    log_input_props_names = ['blocking_status_list', 'block_to_date', 'reason']

    objects_exceptions = (Registry.Administrative.DOMAIN_ID_NOT_FOUND,
                          Registry.Administrative.DOMAIN_ID_NOT_BLOCKED)

    action_name = _('Change blocking')


class ProcessUnblockView(AdministrativeBlockingBaseView):
    form_class = DomainUnblockForm
    corba_function_name = 'unblockDomainsId'
    corba_function_arguments = ['objects', 'new_holder', 'remove_admin_contacts', 'reason']

    log_req_type = 'DomainsUnblock'
    log_input_props_names = ['new_holder', 'remove_admin_contacts', 'reason']

    objects_exceptions = (Registry.Administrative.DOMAIN_ID_NOT_FOUND,
                          Registry.Administrative.DOMAIN_ID_NOT_BLOCKED)
    field_exceptions = {Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS: 'new_holder'}

    action_name = _('Unblock')

    def initialize_log_req(self, form):
        super(ProcessUnblockView, self).initialize_log_req(form)
        self.props.append(('restore_prev_state', False))


class ProcessUnblockAndRestorePrevStateView(AdministrativeBlockingBaseView):
    form_class = DomainUnblockAndRestorePrevStateForm
    corba_function_name = 'restorePreAdministrativeBlockStatesId'
    corba_function_arguments = ['objects', 'new_holder', 'reason']

    log_req_type = 'DomainsUnblock'
    log_input_props_names = ['new_holder', 'reason']

    objects_exceptions = (Registry.Administrative.DOMAIN_ID_NOT_FOUND,
                          Registry.Administrative.DOMAIN_ID_NOT_BLOCKED)
    field_exceptions = {Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS: 'new_holder'}

    action_name = _('Unblock and restore prev. state')

    def initialize_log_req(self, form):
        super(ProcessUnblockAndRestorePrevStateView, self).initialize_log_req(form)
        self.props.append(('restore_prev_state', True))


class ProcessBlacklistAndDeleteView(AdministrativeBlockingBaseView):
    form_class = DomainBlacklistAndDeleteForm
    corba_function_name = 'blacklistAndDeleteDomainsId'
    corba_function_arguments = ['objects', 'blacklist_to_date', 'reason']

    log_req_type = 'DomainsBlacklistAndDelete'
    log_input_props_names = ['blacklist_to_date', 'reason']

    objects_exceptions = (Registry.Administrative.DOMAIN_ID_NOT_FOUND,)
    field_exceptions = {Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS: 'new_holder'}

    action_name = _('Blacklist and delete')
