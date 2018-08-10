"""
    Module mappings.py.
    Provides dictionaries that map classes used in webadmin to their respective
    corba counterparts.

    doctest:

    >>> filter_type_items == [{'classname': 'filter', 'item': ccReg.FT_FILTER},\
 {'classname': 'registrar', 'item': ccReg.FT_REGISTRAR},\
 {'classname': 'obj', 'item': ccReg.FT_OBJ},\
 {'classname': 'contact', 'item': ccReg.FT_CONTACT},\
 {'classname': 'nsset', 'item': ccReg.FT_NSSET},\
 {'classname': 'keyset', 'item': ccReg.FT_KEYSET},\
 {'classname': 'domain', 'item': ccReg.FT_DOMAIN},\
 {'classname': 'invoice', 'item': ccReg.FT_INVOICE},\
 {'classname': 'publicrequest', 'item': ccReg.FT_PUBLICREQUEST},\
 {'classname': 'mail', 'item': ccReg.FT_MAIL},\
 {'classname': 'file', 'item': ccReg.FT_FILE},\
 {'classname': 'logger', 'item': ccReg.FT_LOGGER},\
 {'classname': 'session', 'item': ccReg.FT_SESSION},\
 {'classname': 'zone', 'item': ccReg.FT_ZONE},\
 {'classname': 'message', 'item': ccReg.FT_MESSAGE}]
    True
"""

import sys
from pprint import pprint

from fred_idl import Registry, ccReg
from fred_webadmin.translation import _



def corbaname_to_classname(corbaname):
    """ Return classname (class name in lowercase) for a given ccReg.FT_FILTER*
        type.
    """
    return corbaname._n[3:].lower()


def reverse_dict(dictionary):
    return dict([(value, key) for key, value in dictionary.items()])


filter_type_items = [dict(
    [
        ("classname", corbaname_to_classname(corba_filter_name)),
        ("item", corba_filter_name)
    ]) for corba_filter_name in ccReg.FilterType._items]

#dict {classname: enum_item) where enum_item is item in FilterType (from corba)
# and url is base url of that object
f_name_enum = dict([(item['classname'], item['item']) for
    item in filter_type_items])

# dict {enum_item: classname}
f_enum_name = reverse_dict(f_name_enum)

#dict {classname: id_item) where id_item is item in FilterType (from corba) and
# url is base url of that object
f_name_id = dict([(item['classname'], item['item']._v) for
    item in filter_type_items])

# dict {id_item: classname}
f_id_name = reverse_dict(f_name_id)

# dict {enum_item: url}
f_urls = dict([(name, '/%s/' % (name)) for name in f_name_enum.keys()])
f_urls['group'] = "/group/"
f_urls['contactcheck'] = "/contactcheck/"

# dict {classname: CT_*_ID}, where * is uppercase classname (used in itertable
# headers for 'Id' column)
f_header_ids = dict([(name, 'CT_%s_ID' % (name.upper())) for
    name in f_name_enum.keys()])

# dict {OT_*, classname}, where OT_* is from _Admin.idl ObjectType
f_objectType_name = dict([(item, item._n[3:].lower()) for
    item in Registry.PublicRequest.ObjectType._items])


def generate_dict(suffix):
    """ Returns a dict with (classname -> Classname + suffix) pairs. Note the
        capital letter.

        Anyway, this is really just an utility function to prevent
        boilerplate code.

        doctests:
        >>> generate_dict("TestSuffix") ==  {'session': 'SessionTestSuffix', \
'domain': 'DomainTestSuffix', \
'obj': 'ObjTestSuffix', \
'invoice': 'InvoiceTestSuffix', \
'zone': 'ZoneTestSuffix', \
'file': 'FileTestSuffix', \
'filter': 'FilterTestSuffix', \
'keyset': 'KeySetTestSuffix', \
'contact': 'ContactTestSuffix', \
'registrar': 'RegistrarTestSuffix', \
'nsset': 'NSSetTestSuffix', \
'mail': 'MailTestSuffix', \
'logger': 'LoggerTestSuffix', \
'publicrequest': 'PublicRequestTestSuffix',\
'message': 'MessageTestSuffix'}
        True
    """
    rules = {
        # If more than the first letter should be capitalized, we have to do it
        # manually.
        'nsset': 'NSSet',
        'keyset': 'KeySet',
        'publicrequest': 'PublicRequest',
    }
    result = dict(
        [
            (
                filter_type['classname'],
                rules.get(
                    filter_type['classname'], filter_type['classname'].capitalize()) + suffix)
            for filter_type in filter_type_items
        ])
    return result

f_name_filterformname = generate_dict('FilterForm')
f_name_editformname = generate_dict('EditForm')
f_name_detailname = generate_dict('Detail')

f_name_actionname = generate_dict('')

f_name_req_object_type = dict([(item['classname'], item['classname']) for
    item in filter_type_items])
f_name_req_object_type['logger'] = 'request'
for object_type in ('filter', 'obj', 'session', 'zone'):  # don't log references for these types:
    f_name_req_object_type.pop(object_type)
f_req_object_type_name = reverse_dict(f_name_req_object_type)

# Overwrite some remaining non-matching (class -> action) mappings.
# This is necessary because of tight coupling between class names and action
# types. And names used in Corba would be weird as Python class names here in
# webadmin (e.g. logger is better than request).
# Possible TODO(tomas): refactor to loosen the coupling. PLUS how come it
# matches with filter, edit and detail and not with action?!
f_name_actionname['mail'] = 'Emails'
f_name_actionname['action'] = 'Actions'
f_name_actionname['logger'] = 'Request'

f_name_actionfiltername = dict([(name, actionname + 'Filter') for name, actionname in
                           f_name_actionname.items()])

f_name_actiondetailname = dict([(name, actionname + 'Detail') for name, actionname in
                           f_name_actionname.items()])

f_name_default_sort = {
    'filter': [['Type', 'ASC']],
    'registrar': [['Handle', 'ASC']],
    'obj': [],
    'contact': [['Handle', 'ASC'], ['Create date', 'DESC']],
    'nsset': [['Handle', 'ASC'], ['Create date', 'DESC']],
    'keyset': [['Handle', 'ASC'], ['Create date', 'DESC']],
    'domain': [['FQDN', 'ASC'], ['Create date', 'DESC']],
    'invoice': [['Create Date', 'DESC']],
    'publicrequest': [['Create Time', 'DESC']],
    'mail': [['Create Time', 'DESC']],
    'file': [['Create Time', 'DESC']],
}

f_name_translated_name = {
    'domain': _('domian'),
}

f_name_translated_plural = {
    'domain': _('domains'),
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
        ('f_name_req_object_type', f_name_req_object_type),
    )

    for printed_mapping in printed_mappings:
        print('\n%s:' % printed_mapping[0])
        pprint(printed_mapping[1])
