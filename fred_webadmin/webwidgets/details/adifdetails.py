import cherrypy

from .details import Detail
from dfields import *
from fred_webadmin import nulltype
from fred_webadmin.translation import _
from fred_webadmin.webwidgets.details.sectionlayouts import DirectSectionLayout
from fred_webadmin.webwidgets.details.adifsections import DatesSectionLayout
from fred_webadmin.webwidgets.details.detaillayouts import DirectSectionDetailLayout
from fred_webadmin.webwidgets.details.adifdetaillayouts import DomainsNSSetDetailLayout, DomainsKeySetDetailLayout
from fred_webadmin.webwidgets.adifwidgets import FilterPanel
from fred_webadmin.corbalazy import CorbaLazyRequestIterStructToDict
from fred_webadmin.utils import get_state_id_by_short_name
from fred_webadmin.webwidgets.gpyweb.gpyweb import form, input

# Limit the number of filter results for actions (when pressing the actions
# button) by only asking for the results for the last month.
FILTER_ACTION_TIME_LIMIT_LAST_MONTH = {
    u'Time/4': u'0', u'Time/1/1/0': u'0', u'Time/0/0': u'', u'Time/2': u'',
    u'Time/3': unicode(ccReg.LAST_MONTH._v), u'Time/0/1/1': u'0',
    u'Time/0/1/0': u'0', u'Time/1/0': u'', u'Time/1/1/1': u'0'}

# Limit the number of filter results for e-mails (when pressing the emails
# button) by only asking for the results for the last month.
FILTER_EMAIL_TIME_LIMIT_LAST_MONTH = {
    u'CreateTime/4': u'0', u'CreateTime/1/1/0': u'0', u'CreateTime/0/0': u'', u'CreateTime/2': u'',
    u'CreateTime/3': unicode(ccReg.LAST_MONTH._v), u'CreateTime/0/1/1': u'0',
    u'CreateTime/0/1/0': u'0', u'CreateTime/1/0': u'', u'CreateTime/1/1/1': u'0'}

FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH = {
    u'TimeBegin/4': u'0', u'TimeBegin/1/1/0': u'0', u'TimeBegin/0/0': u'', u'TimeBegin/2': u'',
    u'TimeBegin/3': unicode(ccReg.LAST_MONTH._v), u'TimeBegin/0/1/1': u'0',
    u'TimeBegin/0/1/0': u'0', u'TimeBegin/1/0': u'', u'TimeBegin/1/1/1': u'0'}


class AccessDetail(Detail):
    password = CharDField(label=_('Password'))
    md5Cert = CharDField(label=_('MD5'))  # registrar name


class ZoneDetail(Detail):
    name = CharDField(label=_('Name'))
    credit = CharDField(label=_('Credit'))
    fromDate = DateDField(label=_('From'))
    toDate = DateDField(label=_('To'))


class CertificationDetail(Detail):
    score = CharDField(label=_("Score"))
    fromDate = DateDField(label=_('From'))
    toDate = DateDField(label=_('To'))
    evaluation_file_id = FileHandleDField(
        handle="pdf", label=_('Evaluation'))
    pass


class GroupDetail(Detail):
    name = CharDField(label=_("Name"))


class RegistrarDetail(Detail):
    editable = True

    handle = CharDField(label=_('Handle'))  # registrar identification
    handle_url = ObjectHandleURLDField(label=_('Handle'))

    name = CharDField(label=_('Name'))  # registrar name
    organization = CharDField(label=_('Organization'))  # organization name
    credit = CharDField(label=_('Total credit'))  # credit
    unspec_credit = CharDField(label=_('Unspecified credit'))

    street1 = CharDField(label=_('Street'))  # address part 1
    street2 = CharDField(label='')  # address part 2
    street3 = CharDField(label='')  # address part 3
    city = CharDField(label=_('City'))  # city of registrar headquaters
    stateorprovince = CharDField(label=_('State'))  # address part
    postalcode = CharDField(label=_('ZIP'))  # address part
    country = CharDField(label=_('Country'))  # country code

    telephone = CharDField(label=_('Telephone'))  # phone number
    fax = CharDField(label=_('Fax'))  # fax number
    email = EmailDField(label=_('Email'))  # contact email
    url = CharDField(label=_('URL'))  # URL
    ico = CharDField(label=_('ICO'))
    dic = CharDField(label=_('DIC'))
    varSymb = CharDField(label=_('Var. Symbol'))
    vat = CharDField(label=_('DPH'))
    hidden = CharDField(label=_('System registrar'))  # hidden in PIF

    access = ListObjectDField(detail_class=AccessDetail)
    zones = ListObjectDField(detail_class=ZoneDetail)

    groups = ListObjectDField(detail_class=GroupDetail)

    certifications = ListObjectDField(detail_class=CertificationDetail)

    sections = (
        (None, ('handle', 'organization', 'name', 'credit', 'unspec_credit')),
        (_('Address'), ('street1', 'street2', 'street3', 'city', 'postalcode', 'stateorprovince', 'country')),
        (_('Other_data'), ('telephone', 'fax', 'email', 'url', 'ico', 'dic', 'varSymb', 'vat', 'hidden')),
        (_('Authentication'), ('access',), DirectSectionLayout),
        (_('Zones'), ('zones',), DirectSectionLayout),
        (_('Groups'), ('groups',), DirectSectionLayout),
        (_('Certifications'), ('certifications',), DirectSectionLayout))

    def add_to_bottom(self):
        if self.data:
            self.media_files.append('/js/publicrequests.js')
            ###TODO: This is here temporarily till backandist will create interface for blokcing registrars with history
            if self.data.get('is_blocked'):
                self.add(strong(_('Registrar is blocked.')))
            else:
                self.add(_('Registrar is not blocked.'))
            ### ==
            filters = [[
                [_('Domains sel.'), 'domain', [{'Registrar.Handle': self.data.get('handle')}]],
                [_('Domains cr.'), 'domain', [{'CreateRegistrar.Handle': self.data.get('handle')}]],
                [_('Contact sel.'), 'contact', [{'Registrar.Handle': self.data.get('handle')}]],
                [_('Contact cr.'), 'contact', [{'CreateRegistrar.Handle': self.data.get('handle')}]],
                [_('NSSet sel.'), 'nsset', [{'Registrar.Handle': self.data.get('handle')}]],
                [_('NSSet cr.'), 'nsset', [{'CreateRegistrar.Handle': self.data.get('handle')}]],
                [_('Emails'), 'mail', [
                    {'Message': self.data.get('name'),
                    'CreateTime': FILTER_EMAIL_TIME_LIMIT_LAST_MONTH}]],
                [_('Invoice'), 'invoice', [
                    {'Registrar.Handle': self.data.get('handle')}]],
            ]]

            if self.data.get('is_blocked'):
                filters.append([[_('Unblock'),
                    "javascript:processAction('%s', '%s')" % \
                    (f_urls['registrar'] + 'unblock/?id=%s' % \
                        self.data.get('id'), 'unblock registrar')]])

            self.add(FilterPanel(filters))

        super(RegistrarDetail, self).add_to_bottom()


class ObjectDetail(Detail):
    handle_url = ObjectHandleURLDField(label=_('Handle'))
    handleEPPId = ObjectHandleEPPIdDField(label=('Handle'))
    handle = CharDField(label=_('Handle'))

    registrar = NHDField(
        ObjectDField(
            detail_class=RegistrarDetail,
            display_only=['handle_url', 'name'],
            layout_class=DirectSectionDetailLayout, sections='all_in_one'),
            HistoryObjectDField(detail_class=RegistrarDetail, display_only=['handle_url', 'name']))

    createDate = CharDField(label=_('Create date'))
    updateDate = CharDField(label=_('Update date'))
    transferDate = CharDField(label=_('Transfer date'))
    deleteDate = CharDField(label=_('Delete date'))
    createRegistrar = ObjectDField(label=_('Create_registrar'), detail_class=RegistrarDetail)
    updateRegistrar = ObjectDField(label=('Update_registrar'), detail_class=RegistrarDetail)
    authInfo = CharNHDField(label=_('AuthInfo'))

    states = HistoryStateDField()


class ContactDetail(ObjectDetail):
    organization = DiscloseCharNHDField(label=_('Organization'))
    name = DiscloseCharNHDField(label=_('Name'))
    ident = DiscloseCharNHDField(label=_('Identification data'))

    vat = DiscloseCharNHDField(label=_('DPH'))
    telephone = DiscloseCharNHDField(label=_('Phone'))
    fax = DiscloseCharNHDField(label=_('Fax'))
    email = DiscloseCharNHDField(label=_('Email'))
    notifyEmail = DiscloseCharNHDField(label=_('Notify email'))

    street1 = DiscloseCharNHDField(label=_('Street'), disclose_name='discloseAddress')
    street2 = DiscloseCharNHDField(label='', disclose_name='discloseAddress')
    street3 = DiscloseCharNHDField(label='', disclose_name='discloseAddress')

    postalcode = DiscloseCharNHDField(label=_('ZIP'), disclose_name='discloseAddress')
    city = DiscloseCharNHDField(label=_('City'), disclose_name='discloseAddress')
    country = DiscloseCharNHDField(label=_('Country'), disclose_name='discloseAddress')

    sections = (
        (None, ('handleEPPId', 'organization', 'name', 'ident', 'vat', 'vat', 'telephone', 'fax', 'email', 'notifyEmail', 'authInfo')),
        (_('Selected registrar'), ('registrar',), DirectSectionLayout),
        (_('Dates'), (), DatesSectionLayout),
        (_('Address'), ('street1', 'street2', 'street3', 'postalcode', 'city', 'country')),
        (_('States'), ('states',), DirectSectionLayout)
    )

    def add_to_bottom(self):
        if self.data:
            panel_data = [
                [
                    [_('Domains_owner'), 'domain',
                        [{'Registrant.Handle': self.data.get('handle')}]],
                    [_('Domains_admin'), 'domain',
                        [{'AdminContact.Handle': self.data.get('handle')}]],
                    [_('Domains_all'), 'domain',
                        [{'Registrant.Handle': self.data.get('handle')},
                            {'AdminContact.Handle': self.data.get('handle')},
                            {'TempContact.Handle': self.data.get('handle')}]],
                    [_('NSSets'), 'nsset',
                        [{'TechContact.Handle': self.data.get('handle')}]],
                    [_('KeySets'), 'keyset',
                        [{'TechContact.Handle': self.data.get('handle')}]],
                    [_('Emails'), 'mail',
                        [{'Message': '*%s*' % self.data.get('handle'),
                        'CreateTime': FILTER_EMAIL_TIME_LIMIT_LAST_MONTH}]]\
                ],
                [
                    [_('Public Requests'), 'publicrequest',
                        [{'Object.Handle': self.data.get('handle')}]],
                    [_('Messages'), 'message',
                        [{'MessageContact.Handle': self.data.get('handle')}]]
                ]
            ]
            if not cherrypy.session['user'].check_nperms('read.logger'):
                panel_data.append([
                        [_('UNIX Whois Actions'), 'logger',
                            [{'ServiceType': 0, 'RequestPropertyValue.Name': 'handle',
                                'IsMonitoring': [True, True],
                                'RequestPropertyValue.Value': self.data.get('handle'),
                                'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                        [_('Web Whois Actions'), 'logger',
                            [{'ServiceType': 1, 'RequestPropertyValue.Name': 'handle',
                                'IsMonitoring': [True, True],
                                'RequestPropertyValue.Value': self.data.get('handle'),
                                'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                        [_('Public Req. Actions'), 'logger',
                            [{'ServiceType': 2, 'RequestPropertyValue.Name': 'handle',
                                'IsMonitoring': [True, True],
                                'RequestPropertyValue.Value': self.data.get('handle'),
                                'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                        [_('EPP Actions'), 'logger',
                            [{'ServiceType': 3, 'RequestPropertyValue.Name': 'handle',
                                'IsMonitoring': [True, True],
                                'RequestPropertyValue.Value': self.data.get('handle'),
                                'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                        [_('Webadmin Actions'), 'logger',
                            [{'ServiceType': 4,
                              'IsMonitoring': [True, True],
                              'RequestObjectRef.ObjectType': 'contact',
                              'RequestObjectRef.ObjectId': str(self.data.get('id')),
                              'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                        [_('Intranet Actions'), 'logger',
                            [{'ServiceType': 5, 'RequestPropertyValue.Name': 'handle',
                                'IsMonitoring': [True, True],
                                'RequestPropertyValue.Value': self.data.get('handle'),
                                'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                        [_('MojeID Actions'), 'logger',
                            [{'ServiceType': 6,
                                'IsMonitoring': [True, True],
                                'RequestObjectRef.ObjectType': 'contact',
                                'RequestObjectRef.ObjectId': str(self.data.get('id')),
                                'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                ])
            self.add(FilterPanel(panel_data))
        super(ContactDetail, self).add_to_bottom()


class HostDetail(Detail):
    fqdn = CharDField(label=_('fqdn'))
    inet = ListCharDField(label=_('IP addresses'))


class NSSetDetail(ObjectDetail):
    admins = NHDField(
        ListObjectDField(
            detail_class=ContactDetail,
            display_only=['handle_url', 'organization', 'name', 'email']),
        HistoryListObjectDField(
            detail_class=ContactDetail,
            display_only=['handle_url', 'organization', 'name', 'email']))

    hosts = NHDField(
        ListObjectDField(
            detail_class=HostDetail, display_only=['fqdn', 'inet']),
        HistoryListObjectDField(
            detail_class=HostDetail, display_only=['fqdn', 'inet']))

    reportLevel = CharNHDField(label=_('Report level'))

    sections = (
        (None, ('handleEPPId', 'authInfo', 'reportLevel')),
        (_('Selected registrar'), ('registrar',), DirectSectionLayout),
        (_('Tech. contacts'), ('admins',), DirectSectionLayout),
        (_('Hosts'), ('hosts',), DirectSectionLayout),
        (_('Dates'), ('createRegistrar', 'updateRegistrar'),
            DatesSectionLayout),
        (_('States'), ('states',), DirectSectionLayout)
    )

    def add_to_bottom(self):
        if self.data:
            self.add(FilterPanel([
                [
                    [_('Domains'), 'domain',
                        [{'NSSet.Handle': self.data.get('handle')}]],
                    [_('Emails'), 'mail',
                        [{'Message': self.data.get('handle'),
                        'CreateTime': FILTER_EMAIL_TIME_LIMIT_LAST_MONTH}]]],
                [
                    [_('UNIX Whois Actions'), 'logger',
                        [{'ServiceType': 0, 'RequestPropertyValue.Name': 'handle',
                            'IsMonitoring': [True, True],
                            'RequestPropertyValue.Value': self.data.get('handle'),
                            'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                    [_('Web Whois Actions'), 'logger',
                        [{'ServiceType': 1, 'RequestPropertyValue.Name': 'handle',
                            'IsMonitoring': [True, True],
                            'RequestPropertyValue.Value': self.data.get('handle'),
                            'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                    [_('Public Request Actions'), 'logger',
                        [{'ServiceType': 2, 'RequestPropertyValue.Name': 'handle',
                            'IsMonitoring': [True, True],
                            'RequestPropertyValue.Value': self.data.get('handle'),
                            'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                    [_('EPP Actions'), 'logger',
                        [{'ServiceType': 3, 'RequestPropertyValue.Name': 'handle',
                            'IsMonitoring': [True, True],
                            'RequestPropertyValue.Value': self.data.get('handle'),
                            'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                    [_('Webadmin Actions'), 'logger',
                        [{'ServiceType': 4,
                          'IsMonitoring': [True, True],
                          'RequestObjectRef.ObjectType': 'nsset',
                          'RequestObjectRef.ObjectId': str(self.data.get('id')),
                          'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                    [_('Intranet Actions'), 'logger',
                        [{'ServiceType': 5, 'RequestPropertyValue.Name': 'handle',
                            'IsMonitoring': [True, True],
                            'RequestPropertyValue.Value': self.data.get('handle'),
                            'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]]]
            ]))
        super(NSSetDetail, self).add_to_bottom()


class DSRecordDetail(Detail):
    keyTag = CharDField(label=_('keyTag'))
    alg = CharDField(label=_('algorithm'))
    digestType = CharDField(label=_('digest type'))
    digest = CharDField(label=_('digest'))
    maxSigLife = CharDField(label=_('Max. sig. life'))


class DNSKeyDetail(Detail):
    flags = CharDField(label=_('Flags'))
    protocol = CharDField(label=_('Protocol'))
    alg = CharDField(label=_('Algorithm'))
    key = LongCharDField(label=_('Public key'))


class KeySetDetail(ObjectDetail):
    admins = NHDField(
        ListObjectDField(
            detail_class=ContactDetail,
            display_only=['handle_url', 'organization', 'name', 'email']),
        HistoryListObjectDField(
            detail_class=ContactDetail,
            display_only=['handle_url', 'organization', 'name', 'email']))

    dsrecords = NHDField(
        ListObjectDField(
            detail_class=DSRecordDetail,
            display_only=['keyTag', 'alg', 'digestType', 'digest',
                          'maxSigLife']),
        HistoryListObjectDField(
            detail_class=DSRecordDetail,
            display_only=['keyTag', 'alg', 'digestType', 'digest',
                          'maxSigLife']))

    dnskeys = NHDField(
        ListObjectDField(
            detail_class=DNSKeyDetail,
            display_only=['flags', 'protocol', 'alg', 'key']),
        HistoryListObjectDField(
            detail_class=DNSKeyDetail,
            display_only=['flags', 'protocol', 'alg', 'key']))

    sections = (
        (None, ('handleEPPId', 'authInfo')),
        (_('Selected registrar'), ('registrar',), DirectSectionLayout),
        (_('Tech. contacts'), ('admins',), DirectSectionLayout),
        (_('DS records'), ('dsrecords',), DirectSectionLayout),
        (_('DNSKeys'), ('dnskeys',), DirectSectionLayout),
        (_('Dates'), ('createRegistrar', 'updateRegistrar'), DatesSectionLayout),
        (_('States'), ('states',), DirectSectionLayout)
    )

    def add_to_bottom(self):
        if self.data:
            self.add(FilterPanel([[
                [_('Domains'), 'domain',
                    [{'KeySet.Handle': self.data.get('handle')}]],
                [_('Emails'), 'mail',
                    [{'Message': self.data.get('handle'),
                    'CreateTime': FILTER_EMAIL_TIME_LIMIT_LAST_MONTH}]], ],
                [
                    [_('UNIX Whois Actions'), 'logger',
                        [{'ServiceType': 0, 'RequestPropertyValue.Name': 'handle',
                            'IsMonitoring': [True, True],
                            'RequestPropertyValue.Value': self.data.get('handle'),
                            'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                    [_('Web Whois Actions'), 'logger',
                        [{'ServiceType': 1, 'RequestPropertyValue.Name': 'handle',
                            'IsMonitoring': [True, True],
                            'RequestPropertyValue.Value': self.data.get('handle'),
                            'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                    [_('Public Request Actions'), 'logger',
                        [{'ServiceType': 2, 'RequestPropertyValue.Name': 'handle',
                            'IsMonitoring': [True, True],
                            'RequestPropertyValue.Value': self.data.get('handle'),
                            'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                    [_('EPP Actions'), 'logger',
                        [{'ServiceType': 3, 'RequestPropertyValue.Name': 'handle',
                            'IsMonitoring': [True, True],
                            'RequestPropertyValue.Value': self.data.get('handle'),
                            'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                    [_('Webadmin Actions'), 'logger',
                        [{'ServiceType': 4,
                          'IsMonitoring': [True, True],
                          'RequestObjectRef.ObjectType': 'keyset',
                          'RequestObjectRef.ObjectId': str(self.data.get('id')),
                          'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                    [_('Intranet Actions'), 'logger',
                        [{'ServiceType': 5, 'RequestPropertyValue.Name': 'handle',
                            'IsMonitoring': [True, True],
                            'RequestPropertyValue.Value': self.data.get('handle'),
                            'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]]]
            ]))
        super(KeySetDetail, self).add_to_bottom()


class DomainDetail(ObjectDetail):
    expirationDate = CharNHDField(label=_('Expiration date'))
    valExDate = CharNHDField(label=_('Expir. valuation date'))
    publish = CharNHDField(label=_('In ENUM dictionary'))
    outZoneDate = CharDField(label=_('Out zone date'))

    registrant = NHDField(
        ObjectDField(
            detail_class=ContactDetail,
            display_only=['handle_url', 'organization', 'name'],
            layout_class=DirectSectionDetailLayout, sections='all_in_one'),
        HistoryObjectDField(
            detail_class=ContactDetail,
            display_only=['handle_url', 'organization', 'name']))

    nsset = NHDField(
        ObjectDField(
            detail_class=NSSetDetail,
            display_only=['handle_url', 'registrar', 'admins', 'hosts'],
            layout_class=DomainsNSSetDetailLayout, sections='all_in_one'),
        HistoryObjectDField(
            detail_class=NSSetDetail, display_only=['handle_url']))

    keyset = NHDField(
        ObjectDField(
            detail_class=KeySetDetail,
            display_only=['handle_url', 'registrar', 'admins', 'dsrecords',
                          'dnskeys'],
            layout_class=DomainsKeySetDetailLayout, sections='all_in_one'),
        HistoryObjectDField(
            detail_class=KeySetDetail, display_only=['handle_url']))

    admins = NHDField(
        ListObjectDField(
            detail_class=ContactDetail,
            display_only=['handle_url', 'organization', 'name', 'email']),
        HistoryListObjectDField(
                detail_class=ContactDetail,
                display_only=['handle_url', 'organization', 'name', 'email']))

    temps = NHDField(
        ListObjectDField(
            detail_class=ContactDetail,
            display_only=['handle_url', 'organization', 'name', 'email']),
        HistoryListObjectDField(
                detail_class=ContactDetail,
                display_only=['handle_url', 'organization', 'name', 'email']))

    sections = (
        (None, ('handleEPPId', 'authInfo', 'publish')),
        (_('Dates'), ('createRegistrar', 'updateRegistrar'), DatesSectionLayout),
        (_('Owner'), ('registrant',), DirectSectionLayout),
        (_('Selected registrar'), ('registrar',), DirectSectionLayout),
        (_('Admin contacts'), ('admins',), DirectSectionLayout),
        (_('Temporary contacts'), ('temps',), DirectSectionLayout),
        (_('NSSet'), ('nsset',), DirectSectionLayout),
        (_('KeySet'), ('keyset',), DirectSectionLayout),
        (_('States'), ('states',), DirectSectionLayout),
    )

    def add_to_bottom(self):
        if self.data:
            self.media_files.append('/js/publicrequests.js')
            filter_panel_data = [
                [[_('Emails'), 'mail',
                    [{'Message': self.data.get('handle'),
                    'CreateTime': FILTER_EMAIL_TIME_LIMIT_LAST_MONTH}]],
                [_('dig'), f_urls['domain'] + 'dig/?handle=' + \
                    self.data.get('handle')],
                [_('Set InZone Status'), "javascript:setInZoneStatus('%s')" %
                    (f_urls['domain'] + 'setinzonestatus/?id=%d' % \
                        self.data.get('id'))]],
                [[_('UNIX Whois Actions'), 'logger',
                    [{'ServiceType': 0, 'RequestPropertyValue.Name': 'handle',
                            'IsMonitoring': [True, True],
                        'RequestPropertyValue.Value': self.data.get('handle'),
                        'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                [_('Web Whois Actions'), 'logger',
                    [{'ServiceType': 1, 'RequestPropertyValue.Name': 'handle',
                            'IsMonitoring': [True, True],
                        'RequestPropertyValue.Value': self.data.get('handle'),
                        'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                [_('Public Req. Actions'), 'logger',
                    [{'ServiceType': 2, 'RequestPropertyValue.Name': 'handle',
                            'IsMonitoring': [True, True],
                        'RequestPropertyValue.Value': self.data.get('handle'),
                        'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                [_('EPP Actions'), 'logger',
                    [{'ServiceType': 3, 'RequestPropertyValue.Name': 'handle',
                            'IsMonitoring': [True, True],
                        'RequestPropertyValue.Value': self.data.get('handle'),
                        'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                [_('Webadmin Actions'), 'logger',
                    [{'ServiceType': 4,
                      'IsMonitoring': [True, True],
                      'RequestObjectRef.ObjectType': 'domain',
                      'RequestObjectRef.ObjectId': str(self.data.get('id')),
                      'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]],
                [_('Intranet Actions'), 'logger',
                    [{'ServiceType': 5, 'RequestPropertyValue.Name': 'handle',
                            'IsMonitoring': [True, True],
                        'RequestPropertyValue.Value': self.data.get('handle'),
                        'TimeBegin': FILTER_LOG_REQUEST_TIME_LIMIT_LAST_MONTH}]]]
            ]

            if not cherrypy.session['user'].has_nperm('block.domain'):
                server_block_state_id = get_state_id_by_short_name('serverBlocked')

                server_blocked = False
                if self.data.get('states'):
                    for state in self.data['states']:
                        if state.id == server_block_state_id and isinstance(state.to, nulltype.Null):
                            server_blocked = True
                            break

                if not server_blocked:
                    filter_panel_data.append([[self._get_blocking_form('block')],
                                              [self._get_blocking_form('blacklist_and_delete')],
                                             ])
                else:
                    filter_panel_data.append([[self._get_blocking_form('change_blocking')],
                                              [self._get_blocking_form('unblock')],
                                              [self._get_blocking_form('blacklist_and_delete')],
                                             ])
            self.add(FilterPanel(filter_panel_data))

        super(DomainDetail, self).add_to_bottom()

    def _get_blocking_form(self, blocking_action):
        from fred_webadmin.controller.adif import Domain
        return form(attr(method='post', action='%s/filter/blocking_start/' % f_urls['domain']),
                    input(type='hidden', name='pre_blocking_form', value='1'),
                    input(type='hidden', name='blocking_action', value=blocking_action),
                    input(type='hidden', name='object_selection', value=self.data.get('id')),
                    input(type='submit', value=Domain.blocking_views[blocking_action].action_name),
                   )


class ActionDetail(Detail):
    time = CharDField(label=_('Received_date'))
    registrar = ObjectHandleDField(label=_('Registrar'))
    objectHandle = CharDField(label=_('objectHandle'))
    type = CharDField(label=_('Type'))
    result = CharDField(label=_('Result'))
    clTRID = CharDField(label=_('clTRID'))
    svTRID = CharDField(label=_('svTRID'))
    xml_out = XMLDField(label=_('XML out'))
    xml = XMLDField(label=_('XML in'))

    sections = (
        (None, ('time', 'registrar', 'objectHandle', 'type', 'result',
                'clTRID', 'svTRID')),
        (_('XML In'), ('xml',), DirectSectionLayout),
        (_('XML Out'), ('xml_out',), DirectSectionLayout),
    )


class PublicRequestDetail(Detail):
    id = CharDField(label=_('ID'))
    objects = ListObjectHandleDField(label=_('Objects'))
    type = CorbaEnumDField(label=_('Type'))
    status = CorbaEnumDField(label=_('Status'))
    registrar = ObjectHandleDField(label=_('Registrar'))
    email = CharDField(label=_('Email'))
    answerEmail = ObjectHandleDField(label=_('Answer email'))
    createTime = CharDField(label=_('Create time'))
    resolveTime = CharDField(label=_('Close time'))

    def add_to_bottom(self):
        type_specific_button = None
        if self.data and self.data.get('status') == Registry.PublicRequest.PRS_NEW:
            if self.data.get('type') in (Registry.PublicRequest.PRT_MOJEID_CONTACT_IDENTIFICATION,
                                         Registry.PublicRequest.PRT_CONTACT_IDENTIFICATION):
                type_specific_button = [
                    _('Resend PIN3 Letter (copy)'),
                    "javascript:processAction('%s', 'resend the message')" % \
                        (f_urls['publicrequest'] + 'resend/%s/?id=%s' % \
                            (self.data['type']._n, self.data.get('id')))
                ]
            elif self.data.get('type') in (Registry.PublicRequest.PRT_MOJEID_CONTACT_CONDITIONAL_IDENTIFICATION,
                                           Registry.PublicRequest.PRT_CONTACT_CONDITIONAL_IDENTIFICATION):
                type_specific_button = [
                    _('Resend PIN2 SMS (copy)'),
                    "javascript:processAction('%s', 'resend the message')" % \
                        (f_urls['publicrequest'] + 'resend/%s/?id=%s' % \
                            (self.data['type']._n, self.data.get('id')))
                ]

            self.media_files.append('/js/publicrequests.js')
            buttons = [
                [_('Accept_and_send'),
                    "javascript:processPublicRequest('%s')" % \
                    (f_urls['publicrequest'] + 'resolve/?id=%s' % \
                        self.data.get('id'))],
                [_('Invalidate_and_close'),
                    "javascript:closePublicRequest('%s')" % \
                        (f_urls['publicrequest'] + 'close/?id=%s' % \
                            self.data.get('id'))],
            ]
            if type_specific_button:
                buttons.append(type_specific_button)
            self.add(FilterPanel([buttons]))
        super(PublicRequestDetail, self).add_to_bottom()


class MailDetail(Detail):
    objects = ListCharDField(label=_('Objects'))
    type = ConvertDField(
        label=_('Type'), inner_field=CharDField(),
        convert_table=CorbaLazyRequestIterStructToDict(
            'Mailer', None, 'getMailTypes', ['id', 'name']))
    status = CharDField(label=_('Status'))
    createTime = CharDField(label=_('Create time'))
    modifyTime = CharDField(label=_('Modify time'))
    attachments = ListObjectHandleDField(label=_('Attachments'))
    content = PreCharDField(label=_('Email content'))


class PaymentDetail(Detail):
    number = CharDField(label=_('Number'))
    price = CharDField(label=_('Price'))
    balance = CharDField(label=_('Balance'))


class PaymentActionDetail(Detail):
    paidObject = ObjectHandleDField(label=_('Object'))
    actionTime = CharDField(label=_('Action time'))
    expirationDate = CharDField(label=_('Expiration date'))
    actionType = CharDField(label=_('Action type'))
    unitsCount = CharDField(label=_('Count'))
    pricePerUnit = CharDField(label=_('PPU'))
    price = CharDField(label=_('Price'))


class LoggerDetail(Detail):
    timeBegin = CharDField(label=_('Start time'))
    timeEnd = CharDField(label=_('End time'))
    user_name = CharDField(label=_('Username'))
    action_type = CharDField(label=_('Action type'))
    service_type = CharDField(label=_('Service type'))
    session_id = CharDField(label=_('Session id'))
    sourceIp = CharDField(label=_('Source IP'))
    props = RequestPropertyDField(label=_('Properties'))
    raw_request = XMLDField(label=_("Raw request"))
    raw_response = XMLDField(label=_("Raw response"))
    #result_code = CharDField(label=_('Result code'))
    result_name = CharDField(label=_('Result'))
    refs = ListLogObjectReferenceDField(_('Object references'))

    def check_nperms(self):
        return False
        """
        critical_field = self.fields['service_type']
        nperms = [nperms for nperms in self.get_nperms() if
            nperms.split('.')[-1] == critical_field.get_nperm()]
        return True"""


class BankStatementDetail(Detail):
    accountNumber = CharDField(label=_('Account Number'))
    bankCodeId = CharDField(label=_('Bank Code'))
    code = CharDField(label=_('Code'))
    type = PaymentTypeDField(label=_('Type'))
    konstSym = CharDField(label=_('Constant Symbol'))
    varSymb = CharDField(label=_('Variable Symbol'))
    specSymb = CharDField(label=_('Specific Symbol'))
    price = CharDField(label=_('Price'))
    accountEvid = CharDField(label=_('Account Evid.'))
    accountMemo = CharDField(label=_('Account Memo'))
    accountName = CharDField(label=_('Account Name'))
    invoiceId = ObjectHandleURLDField(
        label=_('Invoice Id'), object_type_name="invoice", id_name="invoiceId",
        handle_name="invoiceId")
    crTime = CharDField(label=_('crTime'))


class SMSDetail(Detail):
    phone_number = CharDField(label=_('Phone number'))
    content = CharDField(label=_('Content'))


class LetterDetail(Detail):
    file = ObjectHandleDField(label=_('PDF'))
    postal_address_name = CharDField(label=_('Name'))
    postal_address_organization = CharDField(label=_('Organization'))
    postal_address_street1 = CharDField(label=_('Street 1'))
    postal_address_street2 = CharDField(label=_('Street 2'))
    postal_address_street3 = CharDField(label=_('Street 3'))
    postal_address_city = CharDField(label=_('City'))
    postal_address_stateorprovince = CharDField(label=_('State or province'))
    postal_address_postalcode = CharDField(label=_('Postal Code'))
    postal_address_country = CharDField(label=_('Country'))
    batch_id = CharDField(label=_('Post service batch id'))


class MessageDetail(Detail):
    createDate = CharDField(label=_('Create Date'))
    modifyDate = CharDField(label=_('Modify Date'))
    attempt = CharDField(label=_('Attempts'))
    status_id = ConvertDField(
        label=_('Status'), inner_field=CharDField(),
        convert_table=CorbaLazyRequestIterStructToDict(
            'Messages', None, 'getStatusList', ['id', 'name']))
    comm_type_id = ConvertDField(
        label=_('Communication type'), inner_field=CharDField(),
        convert_table=CorbaLazyRequestIterStructToDict(
            'Messages', None, 'getCommTypeList', ['id', 'name']))
    message_type_id = ConvertDField(
        label=_('Message type'), inner_field=CharDField(),
        convert_table=CorbaLazyRequestIterStructToDict(
            'Messages', None, 'getMessageTypeList', ['id', 'name']))
#    sms = ObjectDField(detail_class=SMSDetail)
#    letter = ObjectDField(detail_class=LetterDetail)
    message_content = ObjectDField(detail_class={1: SMSDetail, 2: LetterDetail})


class InvoiceDetail(Detail):
    number = CharDField(label=_('Number'))
    registrar = ObjectHandleDField(label=_('Registrar'))
    credit = CharDField(label=_('Credit'))
    createTime = CharDField(label=_('Create date'))
    taxDate = CharDField(label=_('Tax date'))
    fromDate = CharDField(label=_('From date'))
    toDate = CharDField(label=_('To date'))
    type = CorbaEnumDField(label=_('Type'))
    price = PriceDField(label=_('Price'))
    varSymbol = CharDField(label=_('Variable symbol'))
    filePDF = ObjectHandleDField(label=_('XML'))
    fileXML = ObjectHandleDField(label=_('PDF'))
    payments = ListObjectDField(detail_class=PaymentDetail)
    paymentActions = ListObjectDField(detail_class=PaymentActionDetail)

    sections = ((None, ('number', 'registrar', 'credit', 'createTime', 'taxDate', 'fromDate', 'toDate',
                       'type', 'price', 'varSymbol', 'filePDF', 'fileXML')),
                (_('Payments'), ('payments',), DirectSectionLayout),
                (_('Payment actions'), ('paymentActions',), DirectSectionLayout),
               )


detail_classes = [AccessDetail, RegistrarDetail,
                  ObjectDetail,
                  ContactDetail,
                  HostDetail, NSSetDetail,
                  DSRecordDetail, DNSKeyDetail, KeySetDetail,
                  DomainDetail,
                  ActionDetail, PublicRequestDetail, MailDetail,
                  PaymentDetail, PaymentActionDetail, InvoiceDetail,
                  BankStatementDetail, LoggerDetail, ZoneDetail]
