from logging import getLogger
from functools import update_wrapper

import cherrypy


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
        self.args = args
        self.kwargs = kwargs
        return handler(*args, **kwargs)

    def http_method_not_allowed(self, *args, **kwargs):
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
    A mixin that processes a form on POST.
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
