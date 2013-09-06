import cherrypy

from fred_webadmin.controller import views
from fred_webadmin.corba import Registry
from fred_webadmin.mappings import f_urls
from fred_webadmin.translation import _
from fred_webadmin.webwidgets.forms.adifforms import (DomainBlockForm, DomainUnblockForm,
    DomainUnblockAndRestorePrevStateForm, DomainChangeBlockingForm, DomainBlacklistAndDeleteForm)


def context_domain_id_list(exc):
    return {'domain_ids': ', '.join([str(domain_id) for domain_id in exc.what])}


def context_domain_handle_list(exc):
    return {'domain_handles': ', '.join([str(domain.domainHandle) for domain in exc.what])}


def context_owners_other_domains(exc):
    return {
        'holder_handles': ', '.join([str(owner.ownerHandle) for owner in exc.what]),
        'domain_handles': ', '.join([', '.join([str(domain.domainHandle) for domain in owner.otherDomainList])
                              for owner in exc.what]),
    }


DOMAIN_ID_NOT_FOUND_MSG = views.FieldErrMsg('objects', _('Domain(s) with id {domain_ids} not found.'),
                                            context_domain_id_list)
DOMAIN_ID_ALREADY_BLOCKED_MSG = views.FieldErrMsg('objects', _('Domain(s) {domain_handles} are already blocked.'),
                                                  context_domain_handle_list
)
DOMAIN_ID_NOT_BLOCKED_MSG = views.FieldErrMsg('objects', _('Domain {domain_handles} is not blocked.'),
                                              context_domain_handle_list)
NEW_OWNER_DOES_NOT_EXISTS_MSG = views.FieldErrMsg('new_holder', _('New holder {exc.what} does not exists.'))
OWNER_HAS_OTHER_DOMAIN_MSG = views.FieldErrMsg(
    'objects',
    _('Cannot block holder(s) {holder_handles} because theirs domain(s) {domain_handles} are not blocked. '
      'You can create copy of the owner.'),
    context_owners_other_domains
)


class AdministrativeBlockingBaseView(views.ProcessFormCorbaLogView):
    ''' Base class for processing administrative blocking form. '''

    corba_backend_name = 'Blocking'

    success_url = f_urls['domain'] + 'blocking/result/'

    action_name = None  # Translated name of action used for heading and buttons

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


class ProcessBlockView(AdministrativeBlockingBaseView):
    form_class = DomainBlockForm
    corba_function_name = 'blockDomainsId'
    corba_function_arguments = ['objects', 'blocking_status_list', 'owner_block_mode', 'block_to_date', 'reason']

    log_req_type = 'DomainsBlock'
    log_input_props_names = ['blocking_status_list', 'owner_block_mode', 'block_to_date', 'reason']

    field_exceptions = {Registry.Administrative.DOMAIN_ID_NOT_FOUND: DOMAIN_ID_NOT_FOUND_MSG,
                        Registry.Administrative.DOMAIN_ID_ALREADY_BLOCKED: DOMAIN_ID_ALREADY_BLOCKED_MSG,
                        Registry.Administrative.OWNER_HAS_OTHER_DOMAIN: OWNER_HAS_OTHER_DOMAIN_MSG
                       }

    action_name = _('Block')


class ProcessUpdateBlockingView(AdministrativeBlockingBaseView):
    form_class = DomainChangeBlockingForm
    corba_function_name = 'updateBlockDomainsId'
    corba_function_arguments = ['objects', 'blocking_status_list', 'block_to_date', 'reason']

    log_req_type = 'DomainsBlockUpdate'
    log_input_props_names = ['blocking_status_list', 'block_to_date', 'reason']

    field_exceptions = {Registry.Administrative.DOMAIN_ID_NOT_FOUND: DOMAIN_ID_NOT_FOUND_MSG,
                        Registry.Administrative.DOMAIN_ID_NOT_BLOCKED: DOMAIN_ID_NOT_BLOCKED_MSG,
                       }

    action_name = _('Change blocking')


class ProcessUnblockView(AdministrativeBlockingBaseView):
    form_class = DomainUnblockForm
    corba_function_name = 'unblockDomainsId'
    corba_function_arguments = ['objects', 'new_holder', 'remove_admin_contacts', 'reason']

    log_req_type = 'DomainsUnblock'
    log_input_props_names = ['new_holder', 'remove_admin_contacts', 'reason']

    field_exceptions = {Registry.Administrative.DOMAIN_ID_NOT_FOUND: DOMAIN_ID_NOT_FOUND_MSG,
                        Registry.Administrative.DOMAIN_ID_NOT_BLOCKED: DOMAIN_ID_NOT_BLOCKED_MSG,
                        Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS: NEW_OWNER_DOES_NOT_EXISTS_MSG,
                       }

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

    field_exceptions = {Registry.Administrative.DOMAIN_ID_NOT_FOUND: DOMAIN_ID_NOT_FOUND_MSG,
                        Registry.Administrative.DOMAIN_ID_NOT_BLOCKED: DOMAIN_ID_NOT_BLOCKED_MSG,
                        Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS: NEW_OWNER_DOES_NOT_EXISTS_MSG,
                       }

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

    field_exceptions = {Registry.Administrative.DOMAIN_ID_NOT_FOUND: DOMAIN_ID_NOT_FOUND_MSG,
                       }

    action_name = _('Blacklist and delete')
