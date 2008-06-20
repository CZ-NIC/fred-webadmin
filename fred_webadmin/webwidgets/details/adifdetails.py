
from details import Detail
from dfields import *
from fred_webadmin.translation import _

class RegistrarDetail(Detail):
    handle = CharDField(label=_('Handle')) # registrar identification
    name = CharDField(label=_('Name')) # registrar name
    organization = CharDField(label=_('Organization')) # organization name
    credit = CharDField(label=_('Credit')) # organization name

    street1 = CharDField(label=_('Street1')) # address part 1
    street2 = CharDField(label=_('Street2')) # address part 2
    street3 = CharDField(label=_('Street3')) # address part 3
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
    hidden = CharDField(label=_('Hidden in PIF')) # hidden in PIF
    #access = ListObjectDField(label=_('Authentication'), form_class=AccessEditForm, can_delete=True)
    
    sections = (
        (None, ('handle', 'name', 'organization', 'credit')),
        (_('Address'), ('street1', 'street2', 'street3', 'city', 'postalcode', 'stateorprovince', 'country')),
        (_('Other_data'), ('telephone', 'fax', 'email', 'url', 'hidden')),
    )
    
    
class DomainDetail(Detail):
    domain = CharDField(label=_('Domain'))
    registrar = ObjectField(label = _('Selected_registrar'), 
        detail_class=RegistrarDetail, 
        display_only=['name', 'handle'],
    )