import sys
import fred_webadmin.config as config
from pprint import pprint
from omniORB import CORBA, importIDL

importIDL(config.idl)
ccReg = sys.modules['ccReg']

filter_type_items = ccReg.FilterType._items

#dict {classname: enum_item) where enum_item is item in FilterType (from corba) and url is base url of that object  
f_name_enum = dict([(item._n[3:].lower(), item) for item in filter_type_items])

# dict {enum_item: classname}
f_enum_name = dict([(item, item._n[3:].lower()) for item in filter_type_items])

#dict {classname: id_item) where id_item is item in FilterType (from corba) and url is base url of that object  
f_name_id = dict([(item._n[3:].lower(), item._v) for item in filter_type_items])

# dict {id_item: classname}
f_id_name = dict([(item._v, item._n[3:].lower()) for item in filter_type_items])

# dict {enum_item: url} 
f_urls = dict([(name, '/%s/' % (name)) for name in f_name_enum.keys()])

# dict {classname: CT_*_ID}, where * is uppercase classname (usid in itertable headers for 'Id' column)
f_header_ids = dict([(name, 'CT_%s_ID' % (name.upper())) for name in f_name_enum.keys()])

# dict {OT_*, classname}, where OT_* is from _Admin.idl ObjectType 
f_objectType_name = dict([(item, item._n[3:].lower()) for item in ccReg.PublicRequest.ObjectType._items])

f_name_filterformname = dict([(item._n[3:].lower(), item._n[3:].capitalize() + 'FilterForm') for item in filter_type_items])
f_name_filterformname['nsset'] = 'NSSetFilterForm' 
f_name_filterformname['keyset'] = 'KeySetFilterForm' 
f_name_filterformname['publicrequest'] = 'PublicRequestFilterForm' 

f_name_editformname = dict([(item._n[3:].lower(), item._n[3:].capitalize() + 'EditForm') for item in filter_type_items])
f_name_editformname['nsset'] = 'NSSetEditForm' 
f_name_editformname['keyset'] = 'KeySetEditForm' 
f_name_editformname['publicrequest'] = 'PublicRequestEditForm'

f_name_detailname = dict([(item._n[3:].lower(), item._n[3:].capitalize() + 'Detail') for item in filter_type_items])
f_name_detailname['nsset'] = 'NSSetDetail' 
f_name_detailname['keyset'] = 'KeySetDetail' 
f_name_detailname['publicrequest'] = 'PublicRequestDetail'

f_name_actionname =  dict([(item._n[3:].lower(), item._n[3:].capitalize()) for 
                           item in filter_type_items])
f_name_actionname['nsset'] = 'NSSet'
f_name_actionname['mail'] = 'Emails'
f_name_actionname['keyset'] = 'KeySet' 
f_name_actionname['action'] = 'Actions'
f_name_actionname['publicrequest'] = 'PublicRequest'
f_name_actionname['logger'] = 'Request'

f_name_actionfiltername = dict([(key, value + 'Filter') for key, value in
                           f_name_actionname.items()])

f_name_actiondetailname = dict([(key, value + 'Detail') for key, value in
                           f_name_actionname.items()])

# This one will be deleted after getByHanle will be obsolete:
f_name_get_by_handle = {
    'contact': 'getContactByHandle',
    'domain': 'getDomainByFQDN',
    'nsset': 'getNSSetByHandle',
    'registrar': 'getRegistrarByHandle'
}

f_name_default_sort = { 
    'filter': [['Type', 'ASC']],
    'registrar': [['Handle', 'ASC']],
    'obj': [],
    'contact': [['Handle', 'ASC'], ['Create date', 'DESC']],
    'nsset': [['Handle', 'ASC'], ['Create date', 'DESC']],
    'keyset': [['Handle', 'ASC'], ['Create date', 'DESC']],
    #'domain': [['Create date', 'ASC']],
    #'domain': [['Create date', 'DESC']],
    #'domain': [['FQDN', 'ASC'], ['Create date', 'ASC']],
    'domain': [['FQDN', 'ASC'], ['Create date', 'DESC']],
    'action': [['Time', 'DESC']],
    'invoice': [['Create Date', 'DESC']],
    'publicrequest': [['Create Time', 'DESC']],
    'mail': [['Create Time', 'DESC']],    
    'file': [['Create Time', 'DESC']],    
}

if __name__ == '__main__':
    printed_mappings = (
        ('f_name_enum', f_name_enum),
        ('f_enum_name', f_enum_name),
        ('f_name_id', f_name_id),
        ('f_id_name', f_id_name),
        ('f_urls', f_urls),
        ('f_header_ids', f_header_ids),
        ('f_objectType_name', f_objectType_name),
        ('f_name_formname', f_name_editformname),
    )
                        
    for printed_mapping in printed_mappings:
        print('\n%s:' % printed_mapping[0])
        pprint(printed_mapping[1])
    
    
