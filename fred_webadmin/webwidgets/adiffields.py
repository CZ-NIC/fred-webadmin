from fields import Field
from utils import ValidationError
from fred_webadmin.translation import _

class CompoundFilterField(Field):
    "Field that wraps FilterForm inside itself, value of field is data for that form"
    def __init__(self, name='', value=None, form_class=None, *args, **kwargs):
        self.initialized = False
        self.form_class = form_class
        super(CompoundFilterField, self).__init__(name, value, *args, **kwargs)
        self._value = value
        self.form = None
        self.initialized = True
#        self.value = value
        
    def _get_value(self):
        return self._value
    def _set_value(self, value):
        print "!!!!setting value of compound field!!!!"
        self._value = value
        if self.initialized: # to form not instatniate at time, while form classes are being built
            if value is None:
                self.form = self.form_class(is_nested=True)
            else:
                self.form = self.form_class(data=value, is_nested=True)
    value = property(_get_value, _set_value) 
    
    def clean(self, value):
        form = self.form_class(data=value)
        if form.is_valid():
            return form.cleaned_data
        else:
            raise ValidationError(_(u'Correct errors below.'))
    
    def render(self, indent_level=0):
        if not self.form:
            if self.value is None:
                self.form = self.form_class(is_nested=True)
            else:
                self.form = self.form_class(data=self.value, is_nested=True)
            
        print 'renderuju compund field, neboli jeho form'
        return self.form.render(indent_level)

        