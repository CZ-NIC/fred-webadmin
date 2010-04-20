from logging import debug
from formsets import BaseFormSet
from formsetlayouts import TableFormSetLayout
from fields import Field, DecimalField, ChoiceField, MultiValueField, DateField, SplitDateSplitTimeField
from fred_webadmin.webwidgets.utils import ValidationError, ErrorList
from fred_webadmin.translation import _
from fred_webadmin.webwidgets.gpyweb.gpyweb import attr, save, span

#cobra things:
from fred_webadmin.corba import ccReg
INTERVAL_CHOICES = [(choice._v, _(choice._n)) for choice in ccReg.DateTimeIntervalType._items[1:]] # first is None (which means that date is not active)
INTERVAL_CHOICES_DATE_ONLY = [(choice._v, _(choice._n)) for choice in ccReg.DateTimeIntervalType._items[1:]] # first is None (which means that date is not active)
INTERVAL_CHOICES_DATE_ONLY.pop(ccReg.PAST_HOUR._v + -1)
INTERVAL_CHOICES_DATE_ONLY.pop(ccReg.LAST_HOUR._v + -1)

class CompoundFilterField(Field):
    "Field that wraps FilterForm inside itself, value of field is data for that form"
    def __init__(self, name='', value=None, form_class=None, *args, **kwargs):
        self.initialized = False
        self.form_class = form_class
        super(CompoundFilterField, self).__init__(name, value, *args, **kwargs)
        self.parent_form = None
        self._value = value
        self.form = None
        self.initialized = True
#        self.value = value
        
    def _get_value(self):
        return self._value
    def _set_value(self, value):
        self._value = value
        if self.initialized: # to form not instantiate at time, while form classes are being built
            
            if value is None:
                self.form = self.form_class(is_nested=True)
            else:
                data_cleaned = False
                if self.parent_form and self.parent_form.data_cleaned:
                    data_cleaned = True
                self.form = self.form_class(data=value, data_cleaned=data_cleaned, is_nested=True)
    value = property(_get_value, _set_value) 
    
    def clean(self):
        if self.form:
            if self.form.is_valid():
                return self.form.cleaned_data
            else:
                raise ValidationError(_(u'Correct errors below.'))
        elif self.required and not self.value:
            raise ValidationError(_(u'This field is required.'))
    
    def render(self, indent_level=0):
        if not self.form:
            if self.value is None:
                self.form = self.form_class(is_nested=True)
            else:
                self.form = self.form_class(data=self.value, is_nested=True)
            
        debug('Rendering compund field, (its form)')
        return self.form.render(indent_level)

class FormSetField(Field):
    "Field that wraps formset"
    def __init__(self, name='', value='', formset_class=BaseFormSet, 
        formset_layout=TableFormSetLayout, form_class=None, 
        can_order=False, can_delete=False, *args, **kwargs):
    
        self.initialized = False
        self.form_class = form_class
        self.formset_class = formset_class
        self.can_order = can_order
        self.can_delete = can_delete
        self._value = ''
        self._initial = ''
        super(FormSetField, self).__init__(name, value, *args, **kwargs)
        self.formset = None
        self.initialized = True
        self.changed_data_values = []
    
    def create_formset_once(self):
        ''' If formset han't yet been created, this function will create it. '''
        if not self.formset:
            self.formset = self.formset_class(
                data=self.value, initial=self.initial, 
                form_class=self.form_class, prefix=self.name, is_nested=True, 
                can_order=self.can_order, can_delete=self.can_delete)
    
    def _get_value(self):
        return self._value

    def _set_value(self, value):
        if self.value_is_from_initial:
            self._value = ''
        else:
            self._value = value
    value = property(_get_value, _set_value)

    def _get_initial(self):
        return self._initial

    def _set_initial(self, initial):
        if initial:
            for i in range(len(initial)):
                if not isinstance(initial[i], dict):
                    # A little hack to convert object (like from corba) to 
                    # a dictionary, so it is not nessesary to convert it 
                    # manually.
                    initial[i] = initial[i].__dict__ 
        self._initial = initial
    initial = property(_get_initial, _set_initial)
    
    def clean(self):
        self.create_formset_once()
        if self.formset:
            if self.formset.is_valid():
                return self.formset.cleaned_data
            else:
                raise ValidationError(_(u'Correct errors below.'))
        elif self.required and not self.value:
            raise ValidationError(_(u'This field is required.'))
    
    def render(self, indent_level=0):
        self.create_formset_once()
        return self.formset.render(indent_level)

    def value_from_datadict(self, data):
        # Take data dict items starting with self.name to fields 
        # of formsets can access them.
        return dict([[key, val] for key, val in data.items() 
            if key.startswith(self.name)])  

    def _has_changed(self, initial, data):
        """ Returns True if data differs from initial.
        """
        self.create_formset_once()
        for form in self.formset.forms:
            self.changed_data.append

        if data is None:
            data_value = u''
        else:
            data_value = data
        if initial is None:
            initial_value = u''
        else:
            initial_value = initial
        if unicode(initial_value) != unicode(data_value):
            return True
        return False

    def fire_actions(self):
        self.create_formset_once()
        for form in self.formset.forms:
            form.fire_actions()


class CorbaEnumChoiceField(ChoiceField):
    """
    A field created from corba enum type
    """
    def __init__(self, name='', value='', corba_enum=None, required=True, label=None, initial=None, help_text=None, *arg, **kwargs):
        if corba_enum is None:
            raise RuntimeError('corba_enum argument is required!')
        choices = [(unicode(item._v), _(item._n)) for item in corba_enum._items]
        self.corba_enum = corba_enum
        super(CorbaEnumChoiceField, self).__init__(name, value, choices, required, label, initial, help_text, *arg, **kwargs)
        
        
    def clean(self):
        cleaned_data = super(CorbaEnumChoiceField, self).clean()
        if cleaned_data != u'':
            return int(cleaned_data)
    
    def is_empty(self):
        if self.value == self.empty_choice[0]:
            return True
        else:
            return False
            

class AbstractIntervalField(MultiValueField):
    ''' Abstract class field for DateIntervalField and DateTimeIntervalField'''
    def __init__(self, name='', value='', fields=None, *args, **kwargs):
        self.__dict__['content_initialized'] = False
        # fields = (FROM, TO, DAY, TYPE, OFFSET)
 
        super(AbstractIntervalField, self).__init__(name, value, fields, *args, **kwargs)
        self.fields[3].required = True # intertnal type is required
        self.media_files.append('/js/interval_fields.js')
    
    def _set_value(self, value):
        if not value:
            value = [None, None, None, 1, 0]
        super(AbstractIntervalField, self)._set_value(value)
        self.set_iterval_date_display()
    
    def set_from_clean(self, value):
        super(AbstractIntervalField, self).set_from_clean(value)
        self.set_iterval_date_display()
            
    def set_iterval_date_display(self):
        #if hasattr(self, 'date_interval_span'): # when initializing value, make_content method is not yet called, so this checks if it already was
        if self.content_initialized: # when initializing value, make_content method is not yet called, so this checks if it already was
            date_interval_display = 'none'
            date_day_display = 'none'
            date_interval_offset_span = 'none'
            
            if int(self.value[3]) == ccReg.DAY._v: # day
                date_day_display = 'inline'
            elif int(self.value[3]) == ccReg.INTERVAL._v: # not normal interval
                date_interval_display = 'inline'
            elif int(self.value[3]) > ccReg.INTERVAL._v: # not normal interval
                date_interval_offset_span = 'inline'
                    
            
            self.date_interval_span.style = 'display: %s' % date_interval_display
            self.date_day_span.style = 'display: %s' % date_day_display
            self.date_interval_offset_span.style = 'display: %s' % date_interval_offset_span
    
    def make_content(self):
        self.add(self.fields[3],
                 span(attr(cssc='date_interval'),
                      save(self, 'date_interval_span'),
                      _('from') + ':', self.fields[0],
                      _('to') + ':', self.fields[1],
                 ),
                 span(save(self, 'date_interval_offset_span'),
                      attr(cssc='date_interval_offset'), _('offset') + ':', self.fields[4]),
                     
                 span(attr(cssc='date_day'),
                      save(self, 'date_day_span'),
                      _('day') + ':', self.fields[2]
                     ),
                )
        self.content_initialized = True
        self.set_iterval_date_display()
        
    def clean(self):
        cleaned_data = super(AbstractIntervalField, self).clean()
        if cleaned_data and int(cleaned_data[3]) == ccReg.INTERVAL._v and cleaned_data[0] and cleaned_data[1]: # if from and to field filled, and not day filled
            if cleaned_data[0] > cleaned_data[1]: # if from > to
                errors = ErrorList(['"From" must be bigger than "To"'])
                raise ValidationError(errors)
        cleaned_data[3] = int(cleaned_data[3]) # choicefield intervaltype type to int
        cleaned_data[4] = int(cleaned_data[4] or 0) # (offset) decmal to int
            
        return cleaned_data

    def compress(self, data_list):
        return data_list #retrun couple [from, to]
        
    def decompress(self, value):
        return value
    
    def is_empty(self):
        return ((int(self.value[3]) == ccReg.DAY._v and self.fields[2].is_empty()) or 
                (int(self.value[3]) == ccReg.INTERVAL._v and self.fields[0].is_empty() and self.fields[1].is_empty()) or
                (int(self.value[3]) == ccReg.INTERVAL._v and self.fields[4].is_empty())
               )
    

class DateIntervalField(AbstractIntervalField):
    def __init__(self, name='', value='', *args, **kwargs):
        fields = (DateField(size=10), DateField(size=10), DateField(size=10), 
                  ChoiceField(content=[attr(onchange='onChangeDateIntervalType(this)')], choices=INTERVAL_CHOICES_DATE_ONLY), 
                  DecimalField(initial=1, size=5, min_value=-32768, max_value=32767))
        super(DateIntervalField, self).__init__(name, value, fields, *args, **kwargs)
    
class DateTimeIntervalField(AbstractIntervalField):
    def __init__(self, name='', value='', *args, **kwargs):
        fields = (SplitDateSplitTimeField(), SplitDateSplitTimeField(), DateField(size=10), 
                  ChoiceField(content=attr(onchange='onChangeDateIntervalType(this)'), choices=INTERVAL_CHOICES), 
                  DecimalField(initial=1, size=5, min_value=-32768, max_value=32767))
        super(DateTimeIntervalField, self).__init__(name, value, fields, *args, **kwargs)
