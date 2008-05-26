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
    def __init__(self, name='', value='', formset_class = BaseFormSet, formset_layout=TableFormSetLayout, form_class=None, can_order=False, can_delete=False, *args, **kwargs):
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
#        self.value = value
    
    def _get_value(self):
        return self._value
    def _set_value(self, value):
        self._value = value
        if self.value_is_from_initial:
            data = ''
            initial = value
        else:
            data = value
            initial = None
        if self.initialized: # to formset not instantiate at the time, while form classes are being built
            if initial:
                for i in range(len(initial)):
                    if not isinstance(initial[i], dict):
                        initial[i] = initial[i].__dict__ # little hack to convert object (like from corba) to dictionary, so it is not nessesary to convert it manually
            #JE POTREBA ASI SE TADY ZBAVIT TOHO INSTANCIOVANI FORMSETU A NECHAT TO AZ DO self.render, TOTEZ BY SE ASI MELO UDELAT U CompoundFilterField)
            self.formset = self.formset_class(data=data, initial=initial, form_class=self.form_class, prefix=self.name, is_nested=True, can_order=self.can_order, can_delete=self.can_delete)
    value = property(_get_value, _set_value)

    def _get_initial(self):
        return self._initial
    def _set_initial(self, initial):
        if initial:
            import pdb; pdb.set_trace()
            for i in range(len(initial)):
                if not isinstance(initial[i], dict):
                    initial[i] = initial[i].__dict__ # little hack to convert object (like from corba) to dictionary, so it is not nessesary to convert it manually
        self._initial = initial
    initial = property(_get_initial, _set_initial)
    
    def clean(self):
        if self.formset:
            if self.formset.is_valid():
                return self.formset.cleaned_data
            else:
                raise ValidationError(_(u'Correct errors below.'))
        elif self.required and not self.value:
            raise ValidationError(_(u'This field is required.'))
    
    def render(self, indent_level=0):
        if not self.formset:
            self.formset = self.formset_class(data=self.value, form_class=self.form_class, prefix=self.name, is_nested=True, can_order=self.can_order, can_delete=self.can_delete)
            
        debug('Rendering formsetfield')
        return self.formset.render(indent_level)
    def value_from_datadict(self, data):
        return dict([[key, val] for key, val in data.items() if key.startswith(self.name)])  # take data dict items starting with self.name to fields of formsets can access them
    
    
class CorbaEnumChoiceField(ChoiceField):
    """
    A field crated from corba enum type
    """
    def __init__(self, name='', value='', corba_enum=None, required=True, label=None, initial=None, help_text=None, *arg, **kwargs):
        if corba_enum is None:
            raise RuntimeError('corba_enum argument is required!')
        choices = [(unicode(item._v), _(item._n)) for item in corba_enum._items]
        self.corba_enum = corba_enum
        super(CorbaEnumChoiceField, self).__init__(name, value, choices, required, label, initial, help_text, *arg, **kwargs)
        self.empty_choice = ['', '']
        
        
    def clean(self):
        cleaned_data = super(CorbaEnumChoiceField, self).clean()
        if cleaned_data != u'':
            return int(cleaned_data)
    
    def make_content(self):
        if self.required and self.choices and self.choices[0] == self.empty_choice: # remove empty choice:
            self.choices.pop(0)
        elif not self.required and (not self.choices or (self.choices and self.choices[0] != self.empty_choice)): # add empty choice:
            self.choices.insert(0, self.empty_choice)
        super(CorbaEnumChoiceField, self).make_content()
    
    def is_emptry(self):
        if self.value == self.empty_choice[0]:
            return True
        else:
            return False
            
            

class DateIntervalField(MultiValueField):
    def __init__(self, name='', value='', *args, **kwargs):
        fields = (DateField(size=10), DateField(size=10), DateField(size=10), 
                  ChoiceField(content=[attr(onchange='onChangeDateIntervalType(this)')], choices=INTERVAL_CHOICES), 
                  DecimalField(initial=1, size=5, min_value=-32768, max_value=32767)) #first of INTERVAL_CHOICES is HOUR, which has no 
        super(DateIntervalField, self).__init__(name, value, fields, *args, **kwargs)
        self.media_files.append('/js/interval_fields.js')
    
    def _set_value(self, value):
        if not value:
            value = [None, None, None, 1, 0]
        super(DateIntervalField, self)._set_value(value)
        self.set_iterval_date_display()
    
    def set_from_clean(self, value):
        super(DateIntervalField, self).set_from_clean(value)
        self.set_iterval_date_display()
            
    def set_iterval_date_display(self):
        if hasattr(self, 'date_interval_span'): # when initializing value, build_content method is not yet called, so this checks if it already was
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
    
    def build_content(self):
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
        self.set_iterval_date_display()
        
    def clean(self):
        cleaned_data = super(DateIntervalField, self).clean()
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
    
    def is_emptry(self):
        return ((self.value[3] == ccReg.DAY._v and self.fields[0].is_empty()) or 
                (self.value[3] == ccReg.INTERVAL._v and self.fields[1].is_empty() and self.fields[2].is_empty()) or
                (self.value[3] == ccReg.INTERVAL._v and self.fields[4].is_empty())
               )
    

    
class DateTimeIntervalField(DateIntervalField):
    def __init__(self, name='', value='', *args, **kwargs): # pylint: disable-msg=E1003 
        fields = (SplitDateSplitTimeField(), SplitDateSplitTimeField(), DateField(size=10), 
                  ChoiceField(content=attr(onchange='onChangeDateIntervalType(this)'), choices=INTERVAL_CHOICES), 
                  DecimalField(initial=1, size=5, min_value=-32768, max_value=32767))
        # Here is called really parent of parent of this class, to avoid self.fields initialization from parent:
        super(DateIntervalField, self).__init__(name, value, fields, *args, **kwargs)
        self.media_files.append('/js/interval_fields.js')
    
