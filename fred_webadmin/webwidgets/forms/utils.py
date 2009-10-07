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

        Try nested form fields with multiple trees (more forms connected by OR
        operation).

        >>> import datetime
        >>> tmp = [{u'TaxDate': [False, [None, None, \
datetime.date(2009, 10, 14), 1, 0]], \
u'Object': [False, {u'ObjectState': [False, {u'StateId': [False, "empty"]}], \
u'UpdateRegistrar': [False, {u'Name': [False, u'name reg']}]}], \
u'Type': [True, 1]}, {u'Type': [False, 1]}]

        >>> flatten_form_data(tmp)
        [(u'Type', 1, True), \
(u'Object.ObjectState.StateId', 'empty', False), \
(u'Object.UpdateRegistrar.Name', u'name reg', False), \
(u'TaxDate', [None, None, datetime.date(2009, 10, 14), 1, 0], False), \
('or', '', 'False'), (u'Type', 1, False)]



        Try simple form field.

        >>> flatten_form_data([{u'first' : [True, "val"]}])
        [(u'first', 'val', True)]
    """
    field_names = []
    field_values = []
    field_negations = []
    for tree in data:
        for key, value in tree.items():
            field_names.extend(_get_field_names(key, value, sep))
            field_values.extend(_get_values(value))
            field_negations.extend(_get_negations(value))
        field_names.append("or")
        field_values.append("")
        field_negations.append(str(False))
    field_names.pop()
    field_values.pop()
    field_negations.pop()

    flattened_data = []
    # Merge the flattened lists into an array of tuples.
    for index, name in enumerate(field_names):
        flattened_data.append((name, 
            field_values[index],
            field_negations[index]))

    return flattened_data

