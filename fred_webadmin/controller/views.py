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
        return form_class(**self.get_form_kwargs())

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instanciating the form.
        """
        kwargs = {'initial': self.get_initial()}
        if cherrypy.request.method in ('POST', 'PUT'):
            kwargs.update({
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
            raise RuntimeError(
                "No URL to redirect to. Provide a success_url.")
        return url

    def form_valid(self, form):  # pylint: disable=W0613
        raise cherrypy.HTTPRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.get_context_data(form=form)


class ProcessFormView(View, FormMixin):
    """
    A view that processes a form on POST.
    """
    def get(self, *args, **kwargs):  # pylint: disable=W0613
        form_class = self.get_form_class()  # pylint: disable=E1101
        form = self.get_form(form_class)  # pylint: disable=E1101
        return self.get_context_data(form=form)

    def post(self, *args, **kwargs):  # pylint: disable=W0613
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

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
    corba_function_arguments = None  # names of arguments in the form which are passed to CORBA function

    field_exceptions = None  # dict of (corba_excepion_type: FieldErrMsg)

    def __init__(self, **kwargs):
        super(ProcessFormCorbaView, self).__init__(**kwargs)
        if self.field_exceptions is None:
            self.field_exceptions = {}
        if self.field_exceptions is None:
            self.field_exceptions = {}

    def get_corba_function_arguments(self, form):
        return [recoder.u2c(form.cleaned_data[field_name]) for field_name in self.corba_function_arguments]

    def corba_call_success(self, return_value, form):
        pass

    def corba_call_fail(self, exception, form):
        field_err_msg = self.field_exceptions[type(exception)]
        form.add_error(field_err_msg.field_name, field_err_msg.format_msg(exc=exception))

    def form_valid(self, form):
        try:
            return_value = getattr(cherrypy.session[self.corba_backend_name], self.corba_function_name)(
                *self.get_corba_function_arguments(form)
            )
            self.corba_call_success(return_value, form)
            raise cherrypy.HTTPRedirect(self.get_success_url())
        except tuple(self.field_exceptions.keys()), e:
            self.corba_call_fail(e, form)
        return self.get_context_data(form=form)


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
        self.log_req = None
        super(ProcessFormCorbaLogView, self).__init__(**kwargs)

    def initialize_log_req(self, form):
        self.refs.extend([('domain', domain) for domain in form.cleaned_data['objects']])
        for prop_name in self.log_input_props_names:
            prop_value = form.cleaned_data[prop_name]
            if isinstance(prop_value, types.ListType):
                self.props.extend([(prop_name, prop_item_value)
                                   for prop_item_value in form.cleaned_data[prop_name]])
            else:
                self.props.append((prop_name, prop_value))
        self.log_req = utils.create_log_request(self.log_req_type, properties=self.props, references=self.refs)

    def get_corba_function_arguments(self, form):
        corba_arguments = super(ProcessFormCorbaLogView, self).get_corba_function_arguments(form)
        corba_arguments.append(self.log_req.request_id)  # assuming that log_request_id is last argument
        return corba_arguments

    def corba_call_success(self, return_value, form):
        super(ProcessFormCorbaLogView, self).corba_call_success(return_value, form)
        self.log_req.result = 'Success'

    def corba_call_fail(self, exception, form):
        super(ProcessFormCorbaLogView, self).corba_call_fail(exception, form)
        self.log_req.result = 'Fail'
        self.output_props.append(('error', type(exception).__name__))
        self.output_props.append(('error_subject_handle', exception.what))  # pylint: disable=E1101

    def form_valid(self, form):
        self.initialize_log_req(form)
        try:
            return super(ProcessFormCorbaLogView, self).form_valid(form)
        finally:
            self.log_req.close(properties=self.output_props)
