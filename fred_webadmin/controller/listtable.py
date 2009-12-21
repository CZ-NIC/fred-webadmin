import cherrypy
import time
import sys
from logging import debug 

from fred_webadmin import exposed
from fred_webadmin import config

from fred_webadmin.translation import _

import fred_webadmin.webwidgets.forms.utils as form_utils
from fred_webadmin.controller.perms import check_onperm, login_required
from fred_webadmin.webwidgets.forms.filterforms import UnionFilterForm
from fred_webadmin.itertable import IterTable, fileGenerator
from fred_webadmin.mappings import (
    f_name_id, f_name_editformname, f_urls, f_name_actionfiltername, 
    f_name_actiondetailname, f_name_filterformname)
import simplejson
from fred_webadmin.webwidgets.gpyweb.gpyweb import div, p, br
from fred_webadmin.webwidgets.utils import convert_linear_filter_to_form_output
from fred_webadmin.utils import json_response 
from fred_webadmin.webwidgets.adifwidgets import FilterListCustomUnpacked
from fred_webadmin.customview import CustomView
from fred_webadmin.corba import ccReg
from fred_webadmin.utils import get_detail


class ListTableMixin(object):

    __metaclass__ = exposed.AdifPageMetaClass

    def _get_itertable(self, request_object = None):
        if not request_object:
            request_object = self.classname
        key = cherrypy.session.get('corbaSessionString', '')
        
        size = config.tablesize
        user = cherrypy.session.get('user')
        if user and user.table_page_size:
            size = cherrypy.session.get('user').table_page_size

        itertable = IterTable(request_object, key, size)

        return itertable

    def _get_list(self, context, cleaned_filters=None, **kwd):
        table = self._get_itertable()
        show_result = True
        
        try:
            page = int(kwd.get('page', 1))
        except (ValueError, TypeError):
            page = 1
        try:
            sort_col = kwd.get('sort_col')
            if sort_col is not None:
                sort_col = int(kwd.get('sort_col'))
        except (ValueError, TypeError):
            sort_col = 1
        try:
            sort_dir = bool(int(kwd.get('sort_dir', 1)))
        except (ValueError, TypeError):
            sort_dir = True
        
        
        if cleaned_filters is not None:
            table.set_filter(cleaned_filters)
            if kwd.get('save_input'): # save filter
                table.save_filter(kwd['save_input'])
                context['main'].add(_(
                    'Filter saved as "%s"') % kwd['save_input'])
                show_result = False
            else: # normal setting filter
                table.reload()
        if kwd.get('filter_id'): # load filter
            table.load_filter(int(kwd.get('filter_id')))
            if kwd.get('show_form') or not table.all_fields_filled():
                show_result = False
                filter_data = table.get_filter_data()
                form_class = self._get_filterform_class()
                context['form'] = UnionFilterForm(
                    filter_data, data_cleaned=True, form_class=form_class)
            else:
                table.reload()

                
        if kwd.get('cf'):
            table.clear_filter()
        if kwd.get('reload'):
            table.reload()
        if kwd.get('load'): # load current filter from backend
            cleaned_filter_data = table.get_filter_data()
            form_class = self._get_filterform_class()
            form = UnionFilterForm(
                cleaned_filter_data, form_class=form_class, data_cleaned=True)
            context['form'] = form
            context['show_form'] = kwd.get('show_form')
            if config.debug:
                context['main'].add(
                    'kwd_json_data_loaded:', cleaned_filter_data)
        if kwd.get('list_all'):
            table.clear_filter()
            table._table.add()
            table.reload()
        if sort_col is not None:
            table.set_sort(sort_col, sort_dir)

        if show_result:
            if table.num_rows == 0:
                context['result'] = _("No_entries_found")
            if table.num_rows == 1:
                rowId = table.get_row_id(0)
                raise (cherrypy.HTTPRedirect(f_urls[self.classname] + 
                    'detail/?id=%s' % rowId))
            if kwd.get('txt', None):
                cherrypy.response.headers["Content-Type"] = "text/plain"
                cherrypy.response.headers["Content-Disposition"] = \
                    "inline; filename=%s_%s.txt" % (self.classname,
                    time.strftime('%Y-%m-%d'))
                return fileGenerator(table)
            elif kwd.get('csv', None):
                cherrypy.response.headers["Content-Type"] = "text/plain"
                cherrypy.response.headers["Content-Disposition"] = \
                    "attachement; filename=%s_%s.csv" % (
                        self.classname, time.strftime('%Y-%m-%d'))
                return fileGenerator(table)
            table.set_page(page)
            
            context['itertable'] = table
        return context

   
    @check_onperm('read')
    def _filter_json_header(self):
        itertable = self._get_itertable()
        return json_response({
            'header': itertable.header,
            'header_type': itertable.header_type,
            'page_size': itertable.page_size,
            'object_name': itertable.request_object,
        })
    
    @check_onperm('read')
    def _filter_json_rows(self, **kwd):
        debug("A json rows delam s kwd: %s" % kwd)
        itertable = self._get_itertable()
        if kwd.get('sort') is not None and kwd.get('dir') is not None:
            itertable.set_sort_by_name(kwd['sort'], kwd['dir'])
        
        rows = itertable.get_rows_dict(kwd.get('start'), kwd.get('limit'))
        
        json_data = json_response({
            'rows': rows,
            'num_rows': itertable.num_rows,
        })
        debug("vracim json_data = %s" % json_data)
        return json_data
    
    @check_onperm('read')
    def filter(self, *args, **kwd):
        debug('filter ARGS:%s' % unicode(args))

        log_req = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body, 
            f_name_actionfiltername[self.__class__.__name__.lower()])

        if args:
            if args[0] == 'jsondata':
                return self._filter_json_rows(**kwd)
            elif args[0] == 'jsonheader':
                return self._filter_json_header()

        if kwd:
            debug('Incomming data: %s' % kwd)
        context = {'main': div()}
        
        action = 'filter'
        if kwd.get('list_all'):
            action = 'list'

        if kwd.get('txt') or kwd.get('csv'):
            log_req.commit("")
            return self._get_list(context, **kwd)
        elif (kwd.get('cf') or kwd.get('page') or kwd.get('load') or 
              kwd.get('list_all') or kwd.get('filter_id') or
              kwd.get('sort_col')): 
                # clear filter - whole list of objects without using filter form
            context = self._get_list(context, **kwd)
            log_req.commit("")
        else:
            form_class = self._get_filterform_class()
            # bound form with data
            if kwd.get('json_data') or kwd.get('json_linear_filter'):
                if kwd.get('json_linear_filter'):
                    kwd['json_data'] = simplejson.dumps(
                        convert_linear_filter_to_form_output(
                            simplejson.loads(kwd['json_linear_filter'])))
                debug('Form inicializuju datama' % kwd)
                form = UnionFilterForm(kwd, form_class=form_class)
            else:
                form = UnionFilterForm(form_class=form_class)
            context['form'] = form
            if form.is_bound and config.debug:
                context['main'].add(p(u'kwd:' + unicode(kwd)))
            if form.is_valid():
                if config.debug:
                    context['main'].add(p(u'Jsem validni'))
                    context['main'].add(u'cleaned_data:' + unicode(
                        form.cleaned_data), br())
                debug(u'cleaned_data:' + unicode(form.cleaned_data))
                context = self._get_list(context, form.cleaned_data, **kwd)

                context['main'].add(u"rows: " + str(
                    self._get_itertable().num_rows))
                log_req.update("result_size", self._get_itertable().num_rows)
                # Log the selected filters.
                # TODO(tomas): Log OR operators better...
                for name, value, neg in form_utils.flatten_form_data(
                    form.cleaned_data):
                    log_req.update("filter_%s" % name, value)
                    log_req.update("negation", str(neg), child=True)

                log_req.commit("")

                return self._render('filter', context)
            else:
                
                if form.is_bound and config.debug:
                    context['main'].add(u'Jsem nevalidni, errors:' + unicode(
                        form.errors.items()))
                context['headline'] = '%s filter' % self.__class__.__name__
        
        return self._render(action, context)

    @check_onperm('read')
    def allfilters(self, *args, **kwd):
        context = {'main': div()}
        
        itertable = self._get_itertable('filter')
        itertable.set_filter(
            [{'Type': [False, f_name_id[self.classname]]}])
        itertable.reload()
        context['filters_list'] = FilterListCustomUnpacked(
            itertable.get_rows_dict(raw_header=True), self.classname)
        return self._render('allfilters', context)

    @check_onperm('read')
    def detail(self, **kwd):
        req = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body, 
            f_name_actiondetailname[self.__class__.__name__.lower()])

        context = {}
        
        result = self._get_detail(obj_id=kwd.get('id'))

        debug(result)

        req.update("object_id", kwd.get("id"))
        
        context['edit'] = kwd.get('edit', False)
        context['result'] = result
        req.commit("")
        return self._render('detail', context)

    def _get_editform_class(self):
        form_name = f_name_editformname[self.classname]
        form_class = getattr(sys.modules[self.__module__], form_name, None)
        if not form_class:
            raise RuntimeError('No such formclass in modules "%s"' % form_name)
        return form_class
    
    def _get_filterform_class(self):
        form_name = f_name_filterformname[self.classname]
        form_class = getattr(sys.modules[self.__module__], form_name, None)
        if not form_class:
            raise RuntimeError('No such formclass in modules "%s"' % form_name)
        return form_class
    
    @login_required
    def index(self):
        if (config.debug or f_urls.has_key(self.classname)):
            raise cherrypy.HTTPRedirect(f_urls[self.classname] + 'allfilters/')
        else:
            # In production (non-debug) environment we just fall back to 
            # /summary.
            raise NotImplementedError("Support for '%s' has not yet been "
                                      "implemented." % self.classname)

    @check_onperm('read')
    def _get_detail(self, obj_id):
        context = {}
        try:
            obj_id = int(obj_id)
        except (TypeError, ValueError):
            context['main'] = _("Required_integer_as_parameter")
            raise CustomView(self._render('base', ctx=context))

        try:
            return get_detail(self.classname, obj_id)
        except (ccReg.Admin.ObjectNotFound,):
            context['main'] = _("Object_not_found")
            raise CustomView(self._render('base', ctx=context))

