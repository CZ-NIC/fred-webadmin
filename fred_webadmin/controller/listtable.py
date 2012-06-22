import cherrypy
import time
import sys
import omniORB

from fred_webadmin import exposed
from fred_webadmin import config

from fred_webadmin.translation import _

import fred_webadmin.webwidgets.forms.utils as form_utils
from fred_webadmin.controller.perms import check_onperm, login_required
from fred_webadmin.webwidgets.forms.filterforms import UnionFilterForm
from fred_webadmin.itertable import IterTable, fileGenerator
from fred_webadmin.mappings import (
    f_name_id, f_name_editformname, f_urls, f_name_actionfiltername,
    f_name_actiondetailname, f_name_filterformname, f_name_req_object_type)
import simplejson
from fred_webadmin.webwidgets.gpyweb.gpyweb import attr, div, p, h1
from fred_webadmin.webwidgets.utils import convert_linear_filter_to_form_output
from fred_webadmin.webwidgets.adifwidgets import FilterListCustomUnpacked
from fred_webadmin.customview import CustomView
from fred_webadmin.corba import ccReg
from fred_webadmin.utils import get_detail, create_log_request

from fred_webadmin.corbalazy import ServerNotAvailableError
import fred_webadmin.webwidgets.forms.emptyvalue


class ListTableMixin(object):
    """ Implements common functionality for all the classes that support
        filtering and detail displaying.
    """

    __metaclass__ = exposed.AdifPageMetaClass

    def _get_itertable(self, request_object=None):
        if not request_object:
            request_object = self.classname
        key = cherrypy.session.get('corbaSessionString', '')

        size = config.tablesize
        timeout = config.tabletimeout
        user = cherrypy.session.get('user')
        if user and user.table_page_size:
            size = cherrypy.session.get('user').table_page_size

        itertable = IterTable(request_object, key, size, timeout)

        return itertable

    def _get_list(self, context, cleaned_filters=None, in_log_props=None, **kwd):
        log_req = create_log_request(f_name_actionfiltername[self.__class__.__name__.lower()], properties=in_log_props)
        try:
            out_props = []
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
                    props = (('name', kwd['save_input']),
                             ('type', f_name_actionfiltername[self.__class__.__name__.lower()]))
                    save_log_req = create_log_request('SaveFilter', properties=props)
                    try:
                        table.save_filter(kwd['save_input'])
                        save_log_req.result = 'Success'
                    finally:
                        save_log_req.close()
                    context['main'].add(_('Filter saved as "%s"') % kwd['save_input'])
                    show_result = False
                else: # normal setting filter
                    table.reload()

            if kwd.get('filter_id'): # load filter
                # Do not log filter load (Jara's decision - it would just clutter
                # the log output).
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

            log_req.result = 'Success'
            if show_result:
                out_props.append(('result_size', table.num_rows))
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
        except ccReg.Filters.SqlQueryTimeout, e:
            context['main'].add(h1(_('Timeout')),
                                p(_('Database timeout, please try to be more specific about requested data.')))
        finally:
            log_req.close(properties=out_props)
        return context

    @check_onperm('read')
    def filter(self, *args, **kwd):
        context = {'main': div()}
        action = 'list' if kwd.get('list_all') else 'filter'

        if kwd.get('txt') or kwd.get('csv'):
            res = self._get_list(context, **kwd)
            return res
        elif (kwd.get('cf') or kwd.get('page') or kwd.get('load') or
              kwd.get('list_all') or kwd.get('filter_id') or
              kwd.get('sort_col')):
            # clear filter - whole list of objects without using filter form
            context = self._get_list(context, **kwd)
        elif kwd.get("jump_prev") or kwd.get("jump_next"):
            # Increase/decrease the key time field offset and reload the
            # table (jump to the prev./next time interval).
            table = self._get_itertable()
            delta = -1 if kwd.get("jump_prev") else 1
            cleaned_filter_data = table.get_filter_data()
            self._update_key_time_field_offset(
                cleaned_filter_data, kwd['field_name'], delta)
            action = self._process_form(context, action, cleaned_filter_data, **kwd)
        else:
            action = self._process_form(context, action, **kwd)

        return self._render(action, context)

    def _update_key_time_field_offset(self, filter_data, key_field_name,
            delta):
        try:
            key_time_field = filter_data[0][key_field_name]
            key_time_field[1][4] = key_time_field[1][4] + delta
            filter_data[0][key_field_name] = key_time_field
        except IndexError:
            pass

    def _process_form(self, context, action, cleaned_data=None, **kwd):
        form_class = self._get_filterform_class()
        # bound form with data
        if (kwd.get('json_data') or kwd.get('json_linear_filter')):
            if kwd.get('json_linear_filter'):
                kwd['json_data'] = simplejson.dumps(
                    convert_linear_filter_to_form_output(
                        simplejson.loads(kwd['json_linear_filter'])))
            form = UnionFilterForm(kwd, form_class=form_class)
        elif kwd.get('jump_prev') or kwd.get('jump_next'):
            form = UnionFilterForm(
                cleaned_data, form_class=form_class,
                data_cleaned=True)
#            form = UnionFilterForm(
#                form_class=form_class)
        else:
            form = UnionFilterForm(form_class=form_class)
        context['form'] = form
        if form.is_bound and config.debug:
            context['main'].add(p(u'kwd:' + unicode(kwd)))


        valid = form.is_valid()

        if valid:
            in_props = [] # log request properties
            # Log the selected filters.
            # TODO(tomas): Log OR operators better...
            for name, value, neg in form_utils.flatten_form_data(form.cleaned_data):
                in_props.append(('filter_%s' % name, value, False))
                in_props.append(('negation', str(neg), True))

            context = self._get_list(context, form.cleaned_data, in_log_props=in_props, **kwd)
            if config.debug:
                context['main'].add(u"rows: " + str(self._get_itertable().num_rows))

            if self._should_display_jump_links(form):
                # Key time field is active => Display prev/next links.
                key_time_field = form.forms[0].get_key_time_field()
                context['display_jump_links'] = {
                    'url': f_urls[self.classname],
                    'field_name': key_time_field.name}

            action = 'filter'
        else:
            if form.is_bound and config.debug:
                context['main'].add(u'Invalid form data, errors:' + unicode(form.errors.items()))
            context['headline'] = '%s filter' % self.__class__.__name__

        return action

    def _should_display_jump_links(self, form):
        if not (len(form.forms) == 1 and len(form.data) == 1):
            return False
        inner_form = form.forms[0]
        key_time_field = inner_form.get_key_time_field()
        if not key_time_field:
            # Form does not specify a key time field.
            return False
        if not inner_form.fields.get(key_time_field.name):
            # Key time field is not active in the filter.
            return False
        if len(form.cleaned_data) != 1:
            return False
        key_filter_field = form.cleaned_data[0][key_time_field.name][1]
        if isinstance(key_filter_field, fred_webadmin.webwidgets.forms.emptyvalue.FilterFormEmptyValue):
            return False
        if (int(form.cleaned_data[0][key_time_field.name][1][3]) in
                    (int(ccReg.DAY._v), int(ccReg.INTERVAL._v))):
            return False
        return True

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
        log_req = self._create_log_req_for_object_view(**kwd)
        context = {}
        try:
            detail = self._get_detail(obj_id=kwd.get('id'))
            if detail is None:
                log_req.result = 'Fail'
            else:
                log_req.result = 'Success'

            context['edit'] = kwd.get('edit', False)
            context['result'] = detail
        finally:
            log_req.close()
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
