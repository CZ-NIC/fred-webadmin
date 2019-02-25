#
# Copyright (C) 2009-2018  CZ.NIC, z. s. p. o.
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

import cherrypy
import time
import sys
from datetime import datetime

from fred_webadmin import exposed
from fred_webadmin import config

from fred_webadmin.translation import _

import fred_webadmin.webwidgets.forms.emptyvalue
import fred_webadmin.webwidgets.forms.utils as form_utils
from fred_webadmin.controller.perms import check_onperm, login_required
from fred_webadmin.corbarecoder import u2c
from fred_webadmin.webwidgets.forms.filterforms import UnionFilterForm
from fred_webadmin.itertable import IterTable, fileGenerator
from fred_webadmin.mappings import (f_name_id, f_name_editformname, f_urls,
    f_name_actionfiltername, f_name_filterformname)
import simplejson
from fred_webadmin.webwidgets.gpyweb.gpyweb import attr, div, p, h1, script
from fred_webadmin.webwidgets.utils import convert_linear_filter_to_form_output
from fred_webadmin.webwidgets.adifwidgets import FilterListCustomUnpacked
from fred_webadmin.webwidgets.forms.adifforms import ObjectPrintoutForm
from fred_webadmin.customview import CustomView
from fred_webadmin.corba import ccReg, Registry
from fred_webadmin.utils import get_detail, create_log_request, datetime_to_string_with_timezone


class ListTableMixin(object):
    """ Implements common functionality for all the classes that support
        filtering and detail displaying.
    """

    __metaclass__ = exposed.AdifPageMetaClass
    blockable = False  # if object can be administratively blocked

    def _get_itertable(self, request_object=None):
        if not request_object:
            request_object = self.classname
        key = cherrypy.session.get('corbaSessionString', '')

        page_size = config.table_page_size
        timeout = config.table_timeout
        user = cherrypy.session.get('user')
        if user and user.table_page_size:
            page_size = user.table_page_size
        max_row_limit = config.table_max_row_limit_per_obj.get(request_object, config.table_max_row_limit)

        itertable = IterTable(request_object, key, page_size, timeout, max_row_limit)

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
                if kwd.get('save_input'):  # save filter
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
                else:  # normal setting filter
                    table.reload()

            if kwd.get('filter_id'):  # load filter
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
            if kwd.get('load'):  # load current filter from backend
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

                from fred_webadmin.webwidgets.table import WIterTable, WIterTableInForm
                if context.get('blocking_mode'):
                    table.pagination = False
                    action_url = f_urls[self.classname] + 'filter/blocking_start/'
                    success_url = f_urls[self.classname] + 'blocking/'
                    if cherrypy.request.method == 'POST' and kwd.get('pre_blocking_form'):
                        itertable_widget = WIterTableInForm(table, action=action_url,
                                                            data=kwd)
                        if itertable_widget.is_valid():
                            cherrypy.session['pre_blocking_form_data'] = itertable_widget.cleaned_data
                            raise cherrypy.HTTPRedirect(success_url)
                    else:
                        itertable_widget = WIterTableInForm(table, action=action_url)
                else:
                    if table.num_rows == 0:
                        context['result'] = _("No_entries_found")
                    elif table.num_rows == 1:
                        rowId = table.get_row_id(0)
                        raise (cherrypy.HTTPRedirect(f_urls[self.classname] + 'detail/?id=%s' % rowId))
                    if 'txt' in kwd or 'csv' in kwd:
                        cherrypy.response.headers["Content-Type"] = "text/plain"
                        if 'txt' in kwd:
                            cherrypy.response.headers["Content-Disposition"] = \
                                "inline; filename=%s_%s.txt" % (self.classname,
                                                                time.strftime('%Y-%m-%d'))
                        elif 'csv' in kwd:
                            cherrypy.response.headers["Content-Disposition"] = \
                                "attachment; filename=%s_%s.csv" % (self.classname,
                                                                    time.strftime('%Y-%m-%d'))
                        if 'columns' in kwd:
                            columns = kwd['columns'].split('|')
                        else:
                            columns = None
                        return fileGenerator(table, columns)
                    table.set_page(page)
                    itertable_widget = WIterTable(table)

                context['witertable'] = itertable_widget
        except ccReg.Filters.SqlQueryTimeout:
            context['main'].add(h1(_('Timeout')),
                                p(_('Database timeout, please try to be more specific about requested data.')))
        finally:
            log_req.close(properties=out_props)
        return context

    @check_onperm('read')
    def filter(self, *args, **kwd):
        context = {'main': div()}
        action = 'list' if kwd.get('list_all') else 'filter'

        if self.blockable and not cherrypy.session['user'].has_nperm('block.domain'):
            context['blocking_possible'] = True
            if args and args[0] == 'blocking_start':
                context['blocking_mode'] = True

        if kwd.get('txt') or kwd.get('csv'):
            res = self._get_list(context, **kwd)
            return res
        elif (kwd.get('cf') or kwd.get('page') or kwd.get('load') or
              kwd.get('list_all') or kwd.get('filter_id') or
              kwd.get('sort_col') or (args and args[0] == 'blocking_start')):
            # clear filter - whole list of objects without using filter form
            context = self._get_list(context, **kwd)
        elif kwd.get("jump_prev") or kwd.get("jump_next"):
            # Increase/decrease the key time field offset and reload the
            # table (jump to the prev./next time interval).
            table = self._get_itertable()
            delta = -1 if kwd.get("jump_prev") else 1
            cleaned_filter_data = table.get_filter_data()
            self._update_key_time_field_offset(cleaned_filter_data, kwd['field_name'], delta)
            action = self._process_form(context, action, cleaned_filter_data, **kwd)
        else:
            action = self._process_form(context, action, **kwd)

        return self._render(action, context)

    def _update_key_time_field_offset(self, filter_data, key_field_name, delta):
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
        else:
            form = UnionFilterForm(form_class=form_class)
        context['form'] = form
        if form.is_bound and config.debug:
            context['main'].add(p(u'kwd:' + unicode(kwd)))

        valid = form.is_valid()

        if valid:
            in_props = []  # log request properties
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
        if config.debug or self.classname in f_urls:
            raise cherrypy.HTTPRedirect(f_urls[self.classname] + 'allfilters/')
        else:
            # In production (non-debug) environment we just fall back to /summary.
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

    @check_onperm('printout')
    def printout(self, handle, **kwd):
        lang_code = config.lang[:2]
        if lang_code == 'cs':  # conversion between cs and cz identifier of lagnguage
            lang_code = 'cz'
        context = {
            'main': div()
        }
        context['main'].add(script(attr(type='text/javascript'),
            'scwLanguage = "%s"; //sets language of js_calendar' % lang_code,
            'scwDateOutputFormat = "%s"; // set output format for js_calendar' % config.js_calendar_date_format))

        if cherrypy.request.method == 'POST':
            form = ObjectPrintoutForm(data=kwd)
            if form.is_valid():
                for_time = form.cleaned_data['for_time']
                props = [('handle', handle),
                         ('for_time', for_time)]
                log_req = create_log_request('RecordStatement', properties=props)
                try:
                    return self._get_printout_pdf(handle, for_time)
                except Registry.RecordStatement.OBJECT_NOT_FOUND:
                    form.add_error('for_time', _('Object "{}" was not found for the given date.'.format(handle)))
                finally:
                    log_req.close()
        else:
            form = ObjectPrintoutForm()

        context['heading'] = _('Download printout')
        context['form'] = form
        return self._render('printout', context)

    def _get_printout_pdf(self, handle, for_time):
        corba_function = getattr(cherrypy.session['RecordsStatement'], 'historic_{}_printout'.format(self.classname))
        for_time_in_yet_another_fred_datetime_corba_type = Registry.IsoDateTime(
            datetime_to_string_with_timezone(for_time)
        )
        pdf_content = corba_function(u2c(handle), for_time_in_yet_another_fred_datetime_corba_type).data
        cherrypy.response.headers['Content-Type'] = 'application/pdf'
        return pdf_content
