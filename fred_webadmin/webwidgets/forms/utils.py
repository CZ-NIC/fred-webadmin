#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Various utils for web forms. """

__all__ = ["flatten_form_data"]

from fred_webadmin.webwidgets.forms.filterforms import FilterFormEmptyValue


def _get_field_names(key, value, sep='.'):
    """ Construct @sep separated strings from form field names.
        One string for every path from any tree root to a leaf. """
    # It's the last level in the hierarchy
    if not isinstance(value[1], dict):
        return ["%s" % (key,)]

    items = value[1].items()
    return ["%s%s%s" % (key, sep, _get_field_names(k2, v2, 
        sep)[0]) for k2,v2 in items]

def _get_values(value):
    """ Returns an array of form field values. """
    # It's the last level in the hierarchy
    if not isinstance(value[1], dict):
        if isinstance(value[1], FilterFormEmptyValue):
            return [""]
        return [value[1]]

    items = value[1].items()
    return [_get_values(val)[0] for _, val in items]

def _get_negations(value):
    """ For every path from any tree root to a leaf, return it's top-level
        negation flag.
    """
    # It's the last level in the hierarchy
    if not isinstance(value[1], dict):
        return [value[0]]

    items = value[1].items()
    ret = []
    for item in items:
        for _ in _get_negations(item[1]):
            ret.append(value[0])
    return ret

def flatten_form_data(data, sep='.'):
    """
        Flattens the representation of a form's cleaned data to an array of
        (separator separated field name, field value, top level negation flag)
        tuples.

        Args:
            data: Cleaned data of a form. The top-level dictionary is a list of
                tree roots.
                Eg. [{u'TransferTime': [False, "aaa"],
                      u'Handle': [False, "bbb"],
                      u'CreateRegistrar': [False,
                        {u'Handle': [False,
                          {u'blabla' : [False, "value"]}],
                         u'Name': [False,"ddd"]}
                    ]}]
            sep: String separator for the field names.

        Returns:
            [(separator separated field name, field value, top level negation
                flag)].

        Doctests:
    
        Try nested form fields.

        >>> tmp = [{u'TransferTime': [False, "aaa"], \
u'Handle': [False, "bbb"], \
u'CreateRegistrar': [False, \
{u'Handle': [False, \
{u'blabla' : [False, "value"]}], \
u'Name': [False,"ddd"]}] }]

        >>> flatten_form_data(tmp)
        [(u'TransferTime', 'aaa', False),\
 (u'Handle', 'bbb', False),\
 (u'CreateRegistrar.Handle.blabla', 'value', False),\
 (u'CreateRegistrar.Name', 'ddd', False)]

        Try nested form fields with nested negation.

         >>> tmp = [{u'TransferTime': [False, "aaa"], \
u'Handle': [True, "bbb"], \
u'CreateRegistrar': [False, \
{u'Handle': [False, \
{u'blabla' : [True, "value"]}], \
u'Name': [False,"ddd"]}] }]

        >>> flatten_form_data(tmp)
        [(u'TransferTime', 'aaa', False),\
 (u'Handle', 'bbb', True),\
 (u'CreateRegistrar.Handle.blabla', 'value', False),\
 (u'CreateRegistrar.Name', 'ddd', False)]

        Try nested form fields with separator

         >>> tmp = [{u'TransferTime': [False, "aaa"], \
u'Handle': [True, "bbb"], \
u'CreateRegistrar': [False, \
{u'Handle': [False, \
{u'blabla' : [True, "value"]}], \
u'Name': [False,"ddd"]}] }]

        >>> flatten_form_data(tmp, "/")
        [(u'TransferTime', 'aaa', False),\
 (u'Handle', 'bbb', True),\
 (u'CreateRegistrar/Handle/blabla', 'value', False),\
 (u'CreateRegistrar/Name', 'ddd', False)]

        Try simple form field.

        >>> flatten_form_data([{u'first' : [True, "val"]}])
        [(u'first', 'val', True)]
    """
    field_names = []
    field_values = []
    field_negations = []
    for key, value in data[0].items():
        field_names.extend(_get_field_names(key, value, sep))
        field_values.extend(_get_values(value))
        field_negations.extend(_get_negations(value))
    flattened_data = []
    # Merge the flattened lists into an array of tuples.
    for name in field_names:
        index = field_names.index(name)
        flattened_data.append((name, 
            field_values[index],
            field_negations[index]))

    return flattened_data
