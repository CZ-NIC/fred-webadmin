#!/usr/bin/python
# -*- coding: utf-8 -*-

import types
class exposed(type):
    def __init__(cls, name, bases, dict):
        super(exposed, cls).__init__(name, bases, dict)
        for name, value in dict.iteritems():
            if type(value) == types.FunctionType and not name.startswith('_'):
                value.exposed = True
