
from details import Detail
from dfields import *
from fred_webadmin.translation import _
from fred_webadmin.webwidgets.details.sectionlayouts import DirectSectionLayout, SectionLayout
from fred_webadmin.webwidgets.details.adifsections import DatesSectionLayout
from fred_webadmin.webwidgets.details.detaillayouts import DirectSectionDetailLayout, OnlyFieldsDetailLayout
from fred_webadmin.webwidgets.details.adifdetaillayouts import DomainsNSSetDetailLayout, DomainsKeySetDetailLayout
from fred_webadmin.webwidgets.adifwidgets import FilterPanel
from fred_webadmin.corbalazy import CorbaLazyRequestIterStructToDict

class AccessDetail(Detail):
    password = CharDField(label=_('Password'))
    md5Cert = CharDField(label=_('MD5')) # registrar name

class RegistrarDetail(Detail):
    editable = True
    
    handle = CharDField(label=_('Handle')) # registrar identification
    handle_url =  ObjectHandleURLDField(label=_('Handle'))
    
    name = CharDField(label=_('Name')) # registrar name
    organization = CharDField(label=_('Organization')) # organization name
    credit = CharDField(label=_('Credit')) # credit

    street1 = CharDField(label=_('Street')) # address part 1
    street2 = CharDField(label='') # address part 2
    street3 = CharDField(label='') # address part 3
    city = CharDField(label=_('City')) # city of registrar headquaters
    stateorprovince = CharDField(label=_('State')) # address part
    postalcode = CharDField(label=_('ZIP')) # address part
    country = CharDField(label=_('Country')) # country code
    

    telephone = CharDField(label=_('Telephone')) # phne number
    fax = CharDField(label=_('Fax')) # fax number
    email = EmailDField(label=_('Email')) # contact email
    url = CharDField(label=_('URL')) # URL
    ico = CharDField(label=_('ICO'))
    dic = CharDField(label=_('DIC'))
    varSymb = CharDField(label=_('Var. Symbol'))
    vat = CharDField(label=_('DPH'))
    hidden = CharDField(label=_('System registrar')) # hidden in PIF
    
    access = ListObjectDField(detail_class=AccessDetail)
    
    sections = (
        (None, ('handle', 'organization', 'name', 'credit')),
        (_('Address'), ('street1', 'street2', 'street3', 'city', 'postalcode', 'stateorprovince', 'country')),
        (_('Other_data'), ('telephone', 'fax', 'email', 'url', 'ico', 'dic', 'varSymb', 'vat', 'hidden')),
        (_('Authentication'), ('access', ), DirectSectionLayout)
    )

    def add_to_bottom(self):
        if self.data:
            self.add(FilterPanel([
                [_('Domains sel.'), 'domain', [{'Registrar.Handle': self.data.get('handle')}]],
                [_('Domains cr.'), 'domain', [{'CreateRegistrar.Handle': self.data.get('handle')}]],
                [_('Contact sel.'), 'contact', [{'Registrar.Handle': self.data.get('handle')}]],
                [_('Contact cr.'), 'contact', [{'CreateRegistrar.Handle': self.data.get('handle')}]],
                [_('NSSet sel.'), 'nsset', [{'Registrar.Handle': self.data.get('handle')}]],
                [_('NSSet cr.'), 'nsset', [{'CreateRegistrar.Handle': self.data.get('handle')}]],
                #[_('Contacts'), 'contact', [{'Registrar.Handle': self.data.get('handle')}]],
                [_('Actions'), 'action', [{'Registrar.Handle': self.data.get('handle')}]],
                #[_('Emails'), 'mail', [{'Object.Registrar.Handle': self.data.get('handle')}]],
                [_('Emails'), 'mail', [{'Message': self.data.get('name')}]],
            ]))
        super(RegistrarDetail, self).add_to_bottom()

class ObjectDetail(Detail):
    handle_url =  ObjectHandleURLDField(label=_('Handle'))
    handleEPPId = ObjectHandleEPPIdDField(label=('Handle'))
    handle = CharDField(label=_('Handle'))

    #registrar = HistoryObjectDField(label=_('Registrar'), detail_class=RegistrarDetail, display_only=['handle_url', 'name'])
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
        (_('Selected registrar'), ('registrar', ), DirectSectionLayout),
        (_('Dates'), (), DatesSectionLayout),
        (_('Address'), ('street1', 'street2', 'street3', 'postalcode', 'city', 'country')),
        (_('States'), ('states', ), DirectSectionLayout)
    )
    
    def add_to_bottom(self):
        if self.data:
            self.add(FilterPanel([
                [_('Domains_owner'), 'domain', [{'Registrant.Handle': self.data.get('handle')}]],
                [_('Domains_admin'), 'domain', [{'AdminContact.Handle': self.data.get('handle')}]],
                [_('Domains_all'), 'domain', [{'Registrant.Handle': self.data.get('handle')}, {'AdminContact.Handle': self.data.get('handle')}, {'TempContact.Handle': self.data.get('handle')}]],
                [_('NSSets'), 'nsset', [{'TechContact.Handle': self.data.get('handle')}]],
                [_('KeySets'), 'keyset', [{'TechContact.Handle': self.data.get('handle')}]],
                [_('Actions'), 'action', [{'RequestHandle': self.data.get('handle')}]],
                [_('Emails'), 'mail', [{'Message': self.data.get('handle')}]],
            ]))
        super(ContactDetail, self).add_to_bottom()
    
class HostDetail(Detail):
    fqdn = CharDField(label=_('fqdn'))
    inet = ListCharDField(label=_('IP addresses'))

class NSSetDetail(ObjectDetail):
    admins = NHDField(
        ListObjectDField(detail_class=ContactDetail, display_only=['handle_url', 'organization', 'name', 'email']),
        HistoryListObjectDField(detail_class=ContactDetail, display_only=['handle_url', 'organization', 'name', 'email']))
    
    hosts = NHDField(
        ListObjectDField(detail_class=HostDetail, display_only=['fqdn', 'inet']),
        HistoryListObjectDField(detail_class=HostDetail, display_only=['fqdn', 'inet']))

    sections = (
        (None, ('handleEPPId', 'authInfo')),
        (_('Selected registrar'), ('registrar', ), DirectSectionLayout),
        (_('Tech. contacts'), ('admins', ), DirectSectionLayout),
        (_('Hosts'), ('hosts', ), DirectSectionLayout),
        (_('Dates'), ('createRegistrar', 'updateRegistrar'), DatesSectionLayout),
        (_('States'), ('states', ), DirectSectionLayout)
    )
        
    def add_to_bottom(self):
        if self.data:
            self.add(FilterPanel([
                [_('Domains'), 'domain', [{'NSSet.Handle': self.data.get('handle')}]],
                [_('Actions'), 'action', [{'RequestHandle': self.data.get('handle')}]],
                [_('Emails'), 'mail', [{'Message': self.data.get('handle')}]],
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
        ListObjectDField(detail_class=ContactDetail, display_only=['handle_url', 'organization', 'name', 'email']),
        HistoryListObjectDField(detail_class=ContactDetail, display_only=['handle_url', 'organization', 'name', 'email']))
    
    dsrecords = NHDField(
        ListObjectDField(detail_class=DSRecordDetail, display_only=['keyTag', 'alg', 'digestType', 'digest', 'maxSigLife']),
        HistoryListObjectDField(detail_class=DSRecordDetail, display_only=['keyTag', 'alg', 'digestType', 'digest', 'maxSigLife']))

    dnskeys = NHDField(
        ListObjectDField(detail_class=DNSKeyDetail, display_only=['flags', 'protocol', 'alg', 'key']),
        HistoryListObjectDField(detail_class=DNSKeyDetail, display_only=['flags', 'protocol', 'alg', 'key']))
    
    sections = (
        (None, ('handleEPPId', 'authInfo')),
        (_('Selected registrar'), ('registrar', ), DirectSectionLayout),
        (_('Tech. contacts'), ('admins', ), DirectSectionLayout),
        (_('DS records'), ('dsrecords', ), DirectSectionLayout),
        (_('DNSKeys'), ('dnskeys', ), DirectSectionLayout),
        (_('Dates'), ('createRegistrar', 'updateRegistrar'), DatesSectionLayout),
        (_('States'), ('states', ), DirectSectionLayout)
    )
    
    def add_to_bottom(self):
        if self.data:
            self.add(FilterPanel([
                [_('Domains'), 'domain', [{'KeySet.Handle': self.data.get('handle')}]],
                [_('Actions'), 'action', [{'RequestHandle': self.data.get('handle')}]],
                [_('Emails'), 'mail', [{'Message': self.data.get('handle')}]],
            ]))
        super(KeySetDetail, self).add_to_bottom()

class DomainDetail(ObjectDetail):
    expirationDate = CharNHDField(label=_('Expiration date'))
    valExDate = CharNHDField(label=_('Expiration valuation date'))
    outZoneDate = CharDField(label=_('Out zone date'))

    registrant = NHDField(
        ObjectDField(
            detail_class=ContactDetail, 
            display_only=['handle_url', 'organization', 'name'], 
            layout_class=DirectSectionDetailLayout, sections='all_in_one'),
            HistoryObjectDField(detail_class=ContactDetail, display_only=['handle_url', 'organization', 'name']))

    nsset = NHDField(
        ObjectDField(
            detail_class=NSSetDetail, 
            display_only=['handle_url', 'registrar', 'admins', 'hosts'], 
            layout_class=DomainsNSSetDetailLayout, sections='all_in_one'),
            HistoryObjectDField(detail_class=NSSetDetail, display_only=['handle_url']))

    keyset = NHDField(
        ObjectDField(
            detail_class=KeySetDetail, 
            display_only=['handle_url', 'registrar', 'admins', 'dsrecords', 'dnskeys'], 
            layout_class=DomainsKeySetDetailLayout, sections='all_in_one'),
        HistoryObjectDField(detail_class=KeySetDetail, display_only=['handle_url']))
    
    admins = NHDField(
        ListObjectDField(
            detail_class=ContactDetail, 
            display_only=['handle_url', 'organization', 'name', 'email']),
            HistoryListObjectDField(
                detail_class=ContactDetail, 
                display_only=['handle_url', 'organization', 'name', 'email']))
    
    sections = (
        (None, ('handleEPPId', 'authInfo')),
        (_('Dates'), ('createRegistrar', 'updateRegistrar'), DatesSectionLayout),
        (_('Owner'), ('registrant', ), DirectSectionLayout),
        (_('Selected registrar'), ('registrar', ), DirectSectionLayout),
        (_('Admin contacts'), ('admins', ), DirectSectionLayout),
        (_('NSSet'), ('nsset', ), DirectSectionLayout),
        (_('KeySet'), ('keyset', ), DirectSectionLayout),
        (_('States'), ('states', ), DirectSectionLayout),                        
    )
    
    def add_to_bottom(self):
        if self.data:
            self.media_files.append('/js/publicrequests.js')
            self.add(FilterPanel([
                [_('Actions'), 'action', [{'RequestHandle': self.data.get('handle')}]],
                [_('Emails'), 'mail', [{'Message': self.data.get('handle')}]],
                [_('dig'), f_urls['domain'] + 'dig/?handle=' + self.data.get('handle')], 
                [_('Set InZone Status'), "javascript:setInZoneStatus('%s')" % 
                    (f_urls['domain'] + 'setinzonestatus/?id=%d' % self.data.get('id'))],          
            ]))
        super(DomainDetail, self).add_to_bottom()
        

class ActionDetail(Detail):
    time = CharDField(label=_('Received_date'))
    #registrar = ObjectDField(label=('Registrar'), display_only=['handle_url', 'name'], detail_class=RegistrarDetail, layout_class=OnlyFieldsDetailLayout)
    registrar = ObjectHandleDField(label=_('Registrar'))
    objectHandle = CharDField(label=_('objectHandle'))
    type = CharDField(label=_('Type'))
    result = CharDField(label=_('Result'))
    clTRID = CharDField(label=_('clTRID'))
    svTRID = CharDField(label=_('svTRID'))
    xml_out = XMLDField(label=_('XML out'))
    xml = XMLDField(label=_('XML in'))

    sections = (
        (None, ('time', 'registrar', 'objectHandle', 'type', 'result', 'clTRID', 'svTRID')),
        (_('XML In'), ('xml', ), DirectSectionLayout),
        (_('XML Out'), ('xml_out', ), DirectSectionLayout),
    )
    
class PublicRequestDetail(Detail):
    id = CharDField(label=_('ID'))
    objects = ListObjectHandleDField(label=_('Objects'))
    type = CorbaEnumDField(label=_('Type'))
    status = CorbaEnumDField(label=_('Status'))
    registrar = ObjectHandleDField(label=_('Registrar'))
    action = ObjectHandleDField(label=_('Action'))
    email = CharDField(label=_('Email'))
    answerEmail = ObjectHandleDField(label=_('Answer email'))
    createTime = CharDField(label=_('Create time'))
    resolveTime = CharDField(label=_('Close time'))
    
    def add_to_bottom(self):
        if self.data and self.data.get('status') == Registry.PublicRequest.PRS_NEW:
            self.media_files.append('/js/publicrequests.js')
            self.add(FilterPanel([
                [_('Accept_and_send'), "javascript:processPublicRequest('%s')" % (f_urls['publicrequest'] + 'resolve/?id=%s' % self.data.get('id'))],
                [_('Invalidate_and_close'), "javascript:closePublicRequest('%s')" % (f_urls['publicrequest'] + 'close/?id=%s' % self.data.get('id'))],
            ]))
        super(PublicRequestDetail, self).add_to_bottom()
    
class MailDetail(Detail):
    #objects = ListObjectHandleDField(label=_('Objects'))
    objects = ListCharDField(label=_('Objects'))
    type = ConvertDField(label=_('Type'), inner_field=CharDField(), convert_table=CorbaLazyRequestIterStructToDict('Mailer', 'getMailTypes', ['id', 'name']))
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
    action_type = CharDField(label=_('Action type'))
    session_id = CharDField(label=_('Session id'))
#    props = ListCharDField(label=_('Properties'))
    props = RequestPropertyDField(label=_('Properties'))
    raw_request = CharDField(label=_("Raw request"))
    raw_response = CharDField(label=_("Raw response"))

    (_('Dates'), ('timeBegin', 'timeEnd'), DatesSectionLayout),


class InvoiceDetail(Detail):
    number = CharDField(label=_('Number'))
    registrar = ObjectHandleDField(label=_('Registrar'))
    credit = CharDField(label=_('Credit'))
    createTime = CharDField(label=_('Create date'))
    taxDate = CharDField(label=_('Tex date'))
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
                (_('Payments'), ('payments', ), DirectSectionLayout),
                (_('Payment actions'), ('paymentActions', ), DirectSectionLayout),
               )
    
    
detail_classes = [AccessDetail, RegistrarDetail, 
                  ObjectDetail, 
                  ContactDetail, 
                  HostDetail, NSSetDetail, 
                  DSRecordDetail, DNSKeyDetail, KeySetDetail, 
                  DomainDetail, 
                  ActionDetail, PublicRequestDetail, MailDetail, 
                  PaymentDetail, PaymentActionDetail, InvoiceDetail]
