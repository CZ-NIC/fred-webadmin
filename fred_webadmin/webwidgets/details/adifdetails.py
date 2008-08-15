
from details import Detail
from dfields import *
from fred_webadmin.translation import _
from fred_webadmin.webwidgets.details.sectionlayouts import DirectSectionLayout, SectionLayout
from fred_webadmin.webwidgets.details.adifsections import DatesSectionLayout
from fred_webadmin.webwidgets.details.detaillayouts import DirectSectionDetailLayout
from fred_webadmin.webwidgets.details.adifdetaillayouts import DomainsNSSetDetailLayout, DomainsKeySetDetailLayout
from fred_webadmin.webwidgets.adifwidgets import FilterPanel

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
    
    ico = CharDField(label=_('ICO'))
    dic = CharDField(label=_('DIC'))
    varSymb = CharDField(label=_('Var. Symbol'))
    vat = CharDField(label=_('DPH'))

    telephone = CharDField(label=_('Telephone')) # phne number
    fax = CharDField(label=_('Fax')) # fax number
    email = EmailDField(label=_('Email')) # contact email
    url = CharDField(label=_('URL')) # URL
    hidden = CharDField(label=_('System registrar')) # hidden in PIF
    #access = ListObjectDField(label=_('Authentication'), form_class=AccessEditForm, can_delete=True)
    
    sections = (
        (None, ('handle', 'organization', 'name', 'credit')),
        (_('Address'), ('street1', 'street2', 'street3', 'city', 'postalcode', 'stateorprovince', 'country')),
        (_('Other_data'), ('telephone', 'fax', 'email', 'url', 'hidden')),
    )

    def add_to_bottom(self):
        if self.data:
            self.add(FilterPanel([
                [_('Domains_selected'), 'domain', [{'Registrar.Handle': self.data.get('handle')}]],
                [_('Domains_creating'), 'domain', [{'CreateRegistrar.Handle': self.data.get('handle')}]],
                [_('Contacts'), 'contact', [{'Registrar.Handle': self.data.get('handle')}]],
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
        ObjectDField(       detail_class=RegistrarDetail, display_only=['handle_url', 'name'], layout_class=DirectSectionDetailLayout, sections='all_in_one'),
        HistoryObjectDField(detail_class=RegistrarDetail, display_only=['handle_url', 'name'])
    )
    
    createDate = CharDField(label=_('Create date'))
    updateDate = CharDField(label=_('Update date'))
    transferDate = CharDField(label=_('Transfer date'))
    deleteDate = CharDField(label=_('Delete date'))
    createRegistrar = ObjectDField(label=_('Create_registrar'), detail_class=RegistrarDetail)
    updateRegistrar = ObjectDField(label=('Update_registrar'), detail_class=RegistrarDetail)
    authInfo = CharNHDField(label=_('AuthInfo'))

class ContactDetail(ObjectDetail):
    organization = CharNHDField(label=_('Organization'))
    name = CharNHDField(label=_('Name'))
    ident = CharNHDField(label=_('Identification data'))
    
    vat = CharNHDField(label=_('DPH'))
    telephone = CharNHDField(label=_('Phone'))
    fax = CharNHDField(label=_('Fax'))
    email = CharNHDField(label=_('Email'))
    
    street1 = CharNHDField(label=_('Street'))
    street2 = CharNHDField(label='')
    street3 = CharNHDField(label='')
    
    postalcode = CharNHDField(label=_('ZIP'))
    city = CharNHDField(label=_('City'))
    country = CharNHDField(label=_('Country'))
    
    sections = (
        (None, ('handleEPPId', 'organization', 'name', 'ident', 'vat', 'vat', 'telephone', 'fax', 'email', 'authInfo')),
        (_('Selected registrar'), 'registrar', DirectSectionLayout),
        (_('Dates'), (), DatesSectionLayout),
        (_('Address'), ('street1', 'street2', 'street3', 'postalcode', 'city', 'country')),
        #('Admins', 'admins', DirectSectionLayout),
        #('Temps', 'temps', DirectSectionLayout),
        #('Admin pets', 'admin_pets', DirectSectionLayout),
    )
    
    def add_to_bottom(self):
        if self.data:
            self.add(FilterPanel([
                [_('Domains_owner'), 'domain', [{'Registrant.Handle': self.data.get('handle')}]],
                [_('Domains_admin'), 'domain', [{'AdminContact.Handle': self.data.get('handle')}]],
                [_('Domains_all'), 'domain', [{'Registrant.Handle': self.data.get('handle')}, {'AdminContact.Handle': self.data.get('handle')}]],
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
        HistoryListObjectDField(detail_class=ContactDetail, display_only=['handle_url', 'organization', 'name', 'email']),
    )
    
    hosts = NHDField(
        ListObjectDField(detail_class=HostDetail, display_only=['fqdn', 'inet']),
        HistoryListObjectDField(detail_class=HostDetail, display_only=['fqdn', 'inet']),
    )

    sections = (
        (None, ('handleEPPId', 'authInfo')),
        (_('Selected registrar'), 'registrar', DirectSectionLayout),
        (_('Tech. contacts'), 'admins', DirectSectionLayout),
        (_('Hosts'), 'hosts', DirectSectionLayout),
        (_('Dates'), ('createRegistrar', 'updateRegistrar'), DatesSectionLayout),
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
    
class KeySetDetail(ObjectDetail):
    admins = NHDField(
        ListObjectDField(detail_class=ContactDetail, display_only=['handle_url', 'organization', 'name', 'email']),
        HistoryListObjectDField(detail_class=ContactDetail, display_only=['handle_url', 'organization', 'name', 'email']),
    )
    
    dsrecords = NHDField(
        ListObjectDField(detail_class=DSRecordDetail, display_only=['keyTag', 'alg', 'digestType', 'digest', 'maxSigLife']),
        HistoryListObjectDField(detail_class=DSRecordDetail, display_only=['keyTag', 'alg', 'digestType', 'digest', 'maxSigLife']),
    )
    
    sections = (
        (None, ('handleEPPId', 'authInfo')),
        (_('Selected registrar'), 'registrar', DirectSectionLayout),
        (_('Tech. contacts'), 'admins', DirectSectionLayout),
        (_('DS records'), 'dsrecords', DirectSectionLayout),
        (_('Dates'), ('createRegistrar', 'updateRegistrar'), DatesSectionLayout),
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
        ObjectDField(       detail_class=ContactDetail, display_only=['handle_url', 'organization', 'name'], layout_class=DirectSectionDetailLayout, sections='all_in_one'),
        HistoryObjectDField(detail_class=ContactDetail, display_only=['handle_url', 'organization', 'name'])
    )

    nsset = NHDField(
        ObjectDField(       detail_class=NSSetDetail, display_only=['handle_url', 'registrar', 'admins', 'hosts'], layout_class=DomainsNSSetDetailLayout, sections='all_in_one'),
        HistoryObjectDField(detail_class=NSSetDetail, display_only=['handle_url'])
    )

    keyset = NHDField(
        ObjectDField(       detail_class=KeySetDetail, display_only=['handle_url', 'registrar', 'admins', 'dsrecords'], layout_class=DomainsKeySetDetailLayout, sections='all_in_one'),
        HistoryObjectDField(detail_class=KeySetDetail, display_only=['handle_url'])
    )
    
    admins = NHDField(
        ListObjectDField(detail_class=ContactDetail, display_only=['handle_url', 'organization', 'name', 'email']),
        HistoryListObjectDField(detail_class=ContactDetail, display_only=['handle_url', 'organization', 'name', 'email']),
    )
    
    sections = (
        (None, ('handleEPPId', 'authInfo')),
        (_('Dates'), ('createRegistrar', 'updateRegistrar'), DatesSectionLayout),
        (_('Owner'), 'registrant', DirectSectionLayout),
        (_('Selected registrar'), 'registrar', DirectSectionLayout),
        (_('Admin contacts'), 'admins', DirectSectionLayout),
        (_('NSSet'), 'nsset', DirectSectionLayout),
        (_('KeySet'), 'keyset', DirectSectionLayout),
    )
    
    def add_to_bottom(self):
        if self.data:
            self.add(FilterPanel([
                [_('Actions'), 'action', [{'RequestHandle': self.data.get('handle')}]],
                [_('Emails'), 'mail', [{'Message': self.data.get('handle')}]],
                [_('dig'), f_urls['domain'] + 'dig/?handle=' + self.data.get('handle')]
            ]))
        super(DomainDetail, self).add_to_bottom()
        
    
#class DomainDetail(Detail):
#    name = CharDField(label=_('Domain'))
#    registrar = ObjectDField(label = _('Selected_registrar'), 
#        detail_class=RegistrarDetail, 
#        display_only=['name', 'handle'],
#    )
#class DomainDetail(Detail):
#    authInfo = NHDField(
#        CharDField(label=_('AuthInfo')),
#        HistoryDField(label=_('AuthInfo'), inner_field = CharDField())
#    )
#    #authInfo = HistoryDField(label=_('AuthInfo'), inner_field = CharDField())
#    
#    handle = CharDField(label=_('Domain'))
#    
#    createDate = CharDField(label=_('Create Date'))
#    updateDate = CharDField(label=_('Update Date'))
#    transferDate = CharDField(label=_('Transfer Date'))    
#    
#    registrar = ObjectDField(label=_('Selected_registrar'), 
#        detail_class=RegistrarDetail 
#    )
#    updateRegistrar = ObjectDField(label=('Update_registrar'), 
#        detail_class=RegistrarDetail 
#    )    
#    createRegistrar = ObjectDField(label=_('Create_registrar'), 
#        detail_class=RegistrarDetail
#    )
#    
#    admins = ListObjectDField(label=_('Admins'), detail_class=ContactDetail, display_only=['handle_url', 'name', 'email'])
#    
#    temps = HistoryObjectDField(label=_('Temps'), detail_class=ContactDetail, display_only=['handle_url', 'name', 'email'])
#    
#    #admin_pets = HistoryDField(label=_('Admin pets'), inner_field=ListObjectDField(detail_class=ContactDetail, display_only=['handle_url', 'name', 'email']))
#    admin_pets = HistoryListObjectDField(label=_('Admin pets (natural)'), detail_class=ContactDetail, display_only=['handle_url', 'name', 'email'])
#        
#    
#    
#    
#    sections = (
#        (None, ('handle', 'authInfo')),
#        ('Registrar', ('registrar', 'updateRegistrar', 'createRegistrar'), AllRegistrarsSectionLayout),
#        ('Admins', 'admins', DirectSectionLayout),
#        ('Temps', 'temps', DirectSectionLayout),
#        ('Admin pets', 'admin_pets', DirectSectionLayout),
#    )