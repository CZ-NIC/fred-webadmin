from fields import Field, DecimalField, ChoiceField, MultiValueField, DateField, SplitDateSplitTimeField
from utils import ValidationError, ErrorList
from fred_webadmin.translation import _
from gpyweb.gpyweb import attr, save, span

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
        print "!!!!setting value of compound field!!!!"
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
            
        print 'renderuju compund field, neboli jeho form'
        return self.form.render(indent_level)



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
    def clean(self):
        cleaned_data = super(CorbaEnumChoiceField, self).clean()
        return int(cleaned_data)

class DateIntervalField(MultiValueField):
    def __init__(self, name='', value='', *args, **kwargs):
        fields = (DateField(size=10), DateField(size=10), DateField(size=10), 
                  ChoiceField(content=[attr(onchange='onChangeDateIntervalType(this)')], choices=INTERVAL_CHOICES), 
                  DecimalField(initial=1, size=5, min_value=-32768, max_value=32767)) #first of INTERVAL_CHOICES is HOUR, which has no 
        super(DateIntervalField, self).__init__(name, value, fields, *args, **kwargs)
        self.media_files.append('/js/interval_fields.js')
    
    def _set_value(self, value):
        print "VVVAL",value, type(value)
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
            
            print "XXX: self.value[3] =", self.value[3]
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
        print "CLEANEDDATA", cleaned_data
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
    
