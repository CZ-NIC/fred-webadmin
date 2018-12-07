#
# Copyright (C) 2013-2018  CZ.NIC, z. s. p. o.
#
# This file is part of FRED.
#
# FRED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FRED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FRED.  If not, see <https://www.gnu.org/licenses/>.

from logging import getLogger
from functools import update_wrapper
import types

import cherrypy

import fred_webadmin.corbarecoder as recoder
from fred_webadmin import utils

logger = getLogger('fred_webadmin.classviews')


class classonlymethod(classmethod):
    def __get__(self, instance, owner):
        if instance is not None:
            raise AttributeError("This method is available only on the view class.")
        return super(classonlymethod, self).__get__(instance, owner)


class View(object):
    """
    Intentionally simple parent class for all views. Only implements
    dispatch-by-method and simple sanity checking.
    """

    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options', 'trace']

    def __init__(self, **kwargs):
        """
        Constructor. Called in the URLconf; can contain helpful extra
        keyword arguments, and other things.
        """
        # Go through keyword arguments, and either save their values to our
        # instance, or raise an error.
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @classmethod
    def as_view(cls, **initkwargs):
        """
        Main entry point for a request-response process.
        """
        # sanitize keyword arguments
        for key in initkwargs:
            if key in cls.http_method_names:
                raise TypeError(u"You tried to pass in the %s method name as a "
                                u"keyword argument to %s(). Don't do that."
                                % (key, cls.__name__))
            if not hasattr(cls, key):
                raise TypeError(u"%s() received an invalid keyword %r" % (
                    cls.__name__, key))

        def view(*args, **kwargs):
            self = cls(**initkwargs)
            if hasattr(self, 'get') and not hasattr(self, 'head'):
                self.head = self.get  # pylint: disable=W0201,E1101
            return self.dispatch(*args, **kwargs)

        # take name and docstring from class
        update_wrapper(view, cls, updated=())

        # and possible attributes set by decorators
        # like csrf_exempt from dispatch
        update_wrapper(view, cls.dispatch, assigned=())
        return view

    def dispatch(self, *args, **kwargs):
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.
        if cherrypy.request.method.lower() in self.http_method_names:
            handler = getattr(self, cherrypy.request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        self.args = args  # pylint: disable=W0201
        self.kwargs = kwargs  # pylint: disable=W0201
        return handler(*args, **kwargs)

    def http_method_not_allowed(self, *args, **kwargs):  # pylint: disable=W0613
        logger.warning('Method Not Allowed (%s): %s', cherrypy.request.method, cherrypy.request.path_info,
            extra={
                'status_code': 405,
                'request': cherrypy.request
            }
        )
        raise cherrypy.HTTPError(405, "Method not allowed (%s): %s." % (cherrypy.request.method,
                                                                        cherrypy.request.path_info))


class FormMixin(object):
    """
    A mixin that provides a way to show and handle a form in a request.
    """

    initial = {}
    form_class = None
    success_url = None

    def __init__(self, **kwargs):  # pylint: disable=W0613
        super(FormMixin, self).__init__(**kwargs)
        self.form = None

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """
        return self.initial.copy()

    def get_form_class(self):
        """
        Returns the form class to use in this view
        """
        return self.form_class

    def get_form(self, form_class):
        """
        Returns an instance of the form to be used in this view.
        """
        self.form = form_class(**self.get_form_kwargs())
        return self.form

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instanciating the form.
        """
        kwargs = {'initial': self.get_initial()}
        if cherrypy.request.method in ('POST', 'PUT'):
            kwargs.update({
                'method': 'post',
                'data': cherrypy.request.params,
                'files': cherrypy.request.body_params,
            })
        return kwargs

    def get_context_data(self, **kwargs):
        return kwargs

    def get_success_url(self):
        if self.success_url:
            url = self.success_url
        else:
            url = cherrypy.url()
        return url

    def form_valid(self):  # pylint: disable=W0613
        raise cherrypy.HTTPRedirect(self.get_success_url())

    def form_invalid(self):
        return self.get_context_data(form=self.form)


class ProcessFormView(FormMixin, View):
    """
    A view that processes a form on POST.
    """
    def get(self, *args, **kwargs):  # pylint: disable=W0613
        form_class = self.get_form_class()  # pylint: disable=E1101
        self.get_form(form_class)  # pylint: disable=E1101
        return self.get_context_data(form=self.form)

    def post(self, *args, **kwargs):  # pylint: disable=W0613
        form_class = self.get_form_class()
        self.get_form(form_class)
        if self.form.is_valid():
            return self.form_valid()
        else:
            return self.form_invalid()

    # PUT is a valid HTTP verb for creating (with a known URL) or editing an
    # object, note that browsers only support POST for now.
    def put(self, *args, **kwargs):
        return self.post(*args, **kwargs)


class FieldErrMsg(object):
    ''' Contains field_name, message and optionally function, that prepares context from exception data.

        context_func is a function, that returns a dictionary, which is passed to msg.format() method as
        keyword arguments.
    '''
    def __init__(self, field_name, msg, context_func=None):
        self.field_name = field_name
        self.msg = msg
        if context_func is not None:
            self.context_func = context_func
        elif not hasattr(self, 'context_func'):  # can be also in class, but must be static method
            self.context_func = None

    def format_msg(self, exc):
        if self.context_func:
            return self.msg.format(**self.context_func(exc))
        else:
            return self.msg.format(exc=exc)


class ProcessFormCorbaView(ProcessFormView):
    '''
    Process form and call CORBA method.
    '''

    corba_backend_name = None
    corba_function_name = None
    corba_function_arguments_names = None  # names of arguments in the form which are passed to CORBA function

    field_exceptions = None  # dict of (corba_excepion_type: FieldErrMsg)

    def __init__(self, **kwargs):
        super(ProcessFormCorbaView, self).__init__(**kwargs)
        if self.field_exceptions is None:
            self.field_exceptions = {}
        if self.field_exceptions is None:
            self.field_exceptions = {}

    def convert_corba_arguments(self, arguments):
        return [recoder.u2c(argument) for argument in arguments]

    def get_corba_function_arguments_names(self):
        return self.corba_function_arguments_names

    def get_corba_function_arguments(self):
        return self.convert_corba_arguments([self.form.cleaned_data[field_name]
                                             for field_name in self.get_corba_function_arguments_names()])

    def get_corba_function_name(self):  # pylint: disable=W0613
        return self.corba_function_name

    def corba_call(self):
        corba_function_name = self.get_corba_function_name()
        corba_function_arguments = self.get_corba_function_arguments()
        return getattr(cherrypy.session[self.corba_backend_name], corba_function_name)(*corba_function_arguments)

    def corba_call_success(self, return_value):
        pass

    def corba_call_fail(self, exception):
        field_err_msg = self.field_exceptions[type(exception)]
        self.form.add_error(field_err_msg.field_name, field_err_msg.format_msg(exc=exception))

    def form_valid(self):
        try:
            return_value = self.corba_call()
            self.corba_call_success(return_value)
            raise cherrypy.HTTPRedirect(self.get_success_url())
        except tuple(self.field_exceptions.keys()), e:
            self.corba_call_fail(e)
        return self.get_context_data(form=self.form)


class ProcessFormCorbaLogView(ProcessFormCorbaView):
    '''
    Process form and call CORBA method and log to Logger.
    '''

    log_req_type = None
    log_input_props_names = None  # list of input properties names for log request

    def __init__(self, **kwargs):
        self.refs = []
        self.props = []
        self.output_props = []  # when FAIL, add exception to this
        self.output_refs = []
        self.log_req = None
        super(ProcessFormCorbaLogView, self).__init__(**kwargs)

    def initialize_log_req(self):
        if self.log_input_props_names:
            for prop_name in self.log_input_props_names:
                prop_value = self.form.cleaned_data[prop_name]
                if isinstance(prop_value, types.ListType):
                    self.props.extend([(prop_name, prop_item_value)
                                       for prop_item_value in self.form.cleaned_data[prop_name]])
                else:
                    self.props.append((prop_name, prop_value))
        self.log_req = utils.create_log_request(self.log_req_type, properties=self.props, references=self.refs)

    def corba_call_success(self, return_value):
        super(ProcessFormCorbaLogView, self).corba_call_success(return_value)
        self.log_req.result = 'Success'

    def corba_call_fail(self, exception):
        super(ProcessFormCorbaLogView, self).corba_call_fail(exception)
        self.log_req.result = 'Fail'
        self.output_props.append(('error', type(exception).__name__))

    def form_valid(self):
        self.initialize_log_req()
        try:
            return super(ProcessFormCorbaLogView, self).form_valid()
        finally:
            self.log_req.close(properties=self.output_props, references=self.output_refs)
