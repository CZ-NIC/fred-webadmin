import csv

from fred_webadmin import messages
from fred_webadmin.controller.views import FieldErrMsg, ProcessFormCorbaLogView
from fred_webadmin.corba import Registry
from fred_webadmin.translation import _
from fred_webadmin.webwidgets.forms.adifforms import ImportNotifEmailsForm


INVALID_EMAILS_MSG = FieldErrMsg(
    'domains_emails',
    _('The file contains these invalid emails: {invalid_emails}'),
    lambda exc: {'invalid_emails': ', '.join([domain_email.email.decode('utf-8') for domain_email in exc.domain_invalid_email_seq])}
)


class ImportNotifEmailsView(ProcessFormCorbaLogView):
    form_class = ImportNotifEmailsForm

    corba_backend_name = 'Notification'
    corba_function_name = 'set_domain_outzone_unguarded_warning_emails'

    log_req_type = 'ImportOutzoneWarningNotificationEmails'

    field_exceptions = {Registry.Notification.DOMAIN_EMAIL_VALIDATION_ERROR: INVALID_EMAILS_MSG}

    def initialize_log_req(self):
        # self.props.append()
        super(ImportNotifEmailsView, self).initialize_log_req()

    def get_context_data(self, **kwargs):
        kwargs['heading'] = _('Import emails for out-of-zone notification')
        kwargs['after_form'] = _('Note: This form imports CSV file containing columns "Id" (Domain ID in the database) and "Email list" (email addresses separated by comma). This file can contain more columns, they are ignored. After the upload, the email adresses are saved to the domain registry. When the domain is near the status "outzone_unguarded" a notification email is sent and the email addresses are deleted.')
        return super(ImportNotifEmailsView, self).get_context_data(**kwargs)

    def get_corba_function_arguments(self):
        domain_email_list = []
        for domain_id, email in self.form.cleaned_data['domains_emails']:
            domain_email_list.append(Registry.Notification.DomainEmail(domain_id, email))

        self.output_props.extend([
            ('Domains count', len(set([domain_email.domain_id for domain_email in domain_email_list]))),
            ('Emails count', len(domain_email_list))
        ])
        return [domain_email_list]

    def corba_call_success(self, return_value):
        messages.success('Emails have been successfully saved. ({Domains count} domains, {Emails count} emails)'
                         .format(**dict(self.output_props)))
        ProcessFormCorbaLogView.corba_call_success(self, return_value)
