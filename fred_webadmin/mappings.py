from corba import ccReg
from pprint import pprint

#dict {classname: enum_item) where enum_item is item in FilterType (from corba) and url is base url of that object  
f_name_enum = dict([(item._n[3:].lower() + 's', item) for item in ccReg.FilterType._items])

# dict {enum_item: classname}
f_enum_name = dict([(item, item._n[3:].lower() + 's') for item in ccReg.FilterType._items])

#dict {classname: id_item) where id_item is item in FilterType (from corba) and url is base url of that object  
f_name_id = dict([(item._n[3:].lower() + 's', item._v) for item in ccReg.FilterType._items])

# dict {id_item: classname}
f_id_name = dict([(item._v, item._n[3:].lower() + 's') for item in ccReg.FilterType._items])

# dict {enum_item: url} 
f_urls = dict([(name, '/%s/' % (name)) for name in f_name_enum.keys()])

# dict {classname: CT_*_ID}, where * is uppercase classname (usid in itertable headers for 'Id' column)
f_header_ids = dict([(name, 'CT_%s_ID' % (name[:-1].upper())) for name in f_name_enum.keys()])

# dict {OT_*, classname}, where OT_* is from _Admin.idl ObjectType 
f_objectType_name = dict([(item, item._n[3:].lower() + 's') for item in ccReg.AuthInfoRequest.ObjectType._items])

if __name__ == '__main__':
    printed_mappings = (
        ('f_name_enum', f_name_enum),
        ('f_enum_name', f_enum_name),
        ('f_name_id', f_name_id),
        ('f_id_name', f_id_name),
        ('f_urls', f_urls),
        ('f_heder_ids', f_header_ids),
        ('f_objectType_name', f_objectType_name),
    )
                        
    for printed_mapping in printed_mappings:
        print('\n%s:' % printed_mapping[0])
        pprint(printed_mapping[1])
    
    
