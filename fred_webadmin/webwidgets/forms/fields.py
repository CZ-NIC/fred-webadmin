#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import types
import time
import datetime
from decimal import Decimal, DecimalException
from logging import debug

from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget, attr, select, option, span, input
from fred_webadmin.webwidgets.utils import ValidationError, ErrorList, isiterable
from fred_webadmin.translation import _

EMPTY_VALUES = (None, '')

class Field(WebWidget):
    creation_counter = 0
    #tattr_list = input.tattr_list
    is_hidden = False
    
    def __init__(self, name='', value='', required=True, label=None, initial=None, help_text=None, *content, **kwd):
        super(Field, self).__init__(*content, **kwd)
        self.tag = ''
        self.required = required
        self.label = label
        self.initial = initial
        self.help_text = help_text
        self.needs_multipart_form = False
        self.order = 0 # order in form, set during form creation
        self.owner_form = None
        self.value_is_from_initial = False
        
        self.name_orig = self.name = name
        if value == '' and initial is not None:
            self.value_is_from_initial = True
            self.value = initial
        else:
            self.value = value
        
        # Increase the creation counter, and save our local copy.
        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1
        
    def clean(self):
        """
        Validates the given value and returns its "cleaned" value as an
        appropriate Python object.

        Raises ValidationError for any errors.
        """
        if self.required and self.value in EMPTY_VALUES:
            raise ValidationError(_(u'This field is required.'))
        return self.value
    
    def set_from_clean(self, value):
        self.value = value
    
    def value_from_datadict(self, data):
        debug('Jsem %s (orig %s) a beru si data %s' % (self.name, self.name_orig, data.get(self.name, None)))
        return data.get(self.name, None)
    
    def is_empty(self):
        return self.value in EMPTY_VALUES
    
    def _has_changed(self, initial, data):
        """
        Return True if data differs from initial.
        """
        # For purposes of seeing whether something has changed, None is
        # the same as an empty string, if the data or inital value we get
        # is None, replace it w/ u''.
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
    
class CharField(Field):
    tattr_list = input.tattr_list
    def __init__(self, name='', value='', max_length=None, min_length=None, strip_spaces=True, *args, **kwargs):
        super(CharField, self).__init__(name, value, *args, **kwargs)
        self.maxlength = self.max_length = max_length # `maxlength' as html tag attribute and max_length as object's attribute
        self.min_length = min_length
        self.tag = self.tag or u'input'
        self.strip_spaces = strip_spaces
        
        if self.tag == u'input':
            self.type = u'text'
             
    def clean(self):
        "Validates max_length and min_length. Returns a Unicode object."
        if self.strip_spaces and isinstance(self.value, types.StringTypes):
            self.value = self.value.strip()
        super(CharField, self).clean()
        if self.is_empty():
            return u''
        value_length = len(self.value)
        if self.max_length is not None and value_length > self.max_length:
            raise ValidationError(_(u'Ensure this value has at most %(max)d characters (it has %(length)d).') % {'max': self.max_length, 'length': value_length})
        if self.min_length is not None and value_length < self.min_length:
            raise ValidationError(_(u'Ensure this value has at least %(min)d characters (it has %(length)d).') % {'min': self.min_length, 'length': value_length})
        return self.value

        
class PasswordField(CharField):
    def __init__(self, name='', value='', max_length=None, min_length=None, *args, **kwargs):
        super(PasswordField, self).__init__(name, value, max_length, min_length, *args, **kwargs)
        if self.tag == u'input':
            self.type = u'password'
            

       
   
class FloatField(Field):
    tattr_list = input.tattr_list
    def __init__(self, name='', value='', max_value=None, min_value=None, *args, **kwargs):
        super(FloatField, self).__init__(name, value, *args, **kwargs)
        self.max_value = max_value
        self.min_value = min_value
        self.tag = self.tag or u'input'
        if self.tag == u'input':
            self.type = u'text'
        
        
    def clean(self):
        """
        Validates that float() can be called on the input. Returns a float.
        Returns None for empty values.
        """
        super(FloatField, self).clean()
        if self.is_empty():
            return None
        try:
            value = float(self.value)
        except (ValueError, TypeError):
            raise ValidationError(_(u'Enter a number.'))
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(_(u'Ensure this value is less than or equal to %s.') % self.max_value)
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(_(u'Ensure this value is greater than or equal to %s.') % self.min_value)
        return value

class DecimalField(Field):
    tattr_list = input.tattr_list
    def __init__(self, name='', value='', max_value=None, min_value=None, max_digits=None, decimal_places=None, *args, **kwargs):
        super(DecimalField, self).__init__(name, value,  *args, **kwargs)
        self.max_value, self.min_value = max_value, min_value
        self.max_digits, self.decimal_places = max_digits, decimal_places
        self.tag = self.tag or u'input'
        if self.tag == u'input':
            self.type = u'text'

    def clean(self):
        """
        Validates that the input is a decimal number. Returns a Decimal
        instance. Returns None for empty values. Ensures that there are no more
        than max_digits in the number, and no more than decimal_places digits
        after the decimal point.
        """
        super(DecimalField, self).clean()
        if self.is_empty():
            return None
        value = unicode(self.value).strip()
        try:
            value = Decimal(value)
        except DecimalException:
            raise ValidationError(_(u'Enter a number.'))
        pieces = unicode(value).lstrip("-").split('.')
        decimals = (len(pieces) == 2) and len(pieces[1]) or 0
        digits = len(pieces[0])
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(_(u'Ensure this value is less than or equal to %s.') % self.max_value)
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(_(u'Ensure this value is greater than or equal to %s.') % self.min_value)
        if self.max_digits is not None and (digits + decimals) > self.max_digits:
            raise ValidationError(_(u'Ensure that there are no more than %s digits in total.') % self.max_digits)
        if self.decimal_places is not None and decimals > self.decimal_places:
            raise ValidationError(_(u'Ensure that there are no more than %s decimal places.') % self.decimal_places)
        if self.max_digits is not None and self.decimal_places is not None and digits > (self.max_digits - self.decimal_places):
            raise ValidationError(_(u'Ensure that there are no more than %s digits before the decimal point.') % (self.max_digits - self.decimal_places))
        return value
    
    def set_from_clean(self, value):
        self.value = unicode(value)
        
class IntegerField(DecimalField):
    def __init__(self, name='', value='', max_value=None, min_value=None, *args, **kwargs):
        super(IntegerField, self).__init__(name='', value='', max_value=max_value, min_value=min_value, decimal_places=0, *args, **kwargs)
    def clean(self):
        return int(super(IntegerField, self).clean())

DEFAULT_DATE_INPUT_FORMATS = (
    u'%d.%m.%Y',                          # '25.10.2006'
    u'%Y-%m-%d', u'%m/%d/%Y', '%m/%d/%y', # '2006-10-25', '10/25/2006', '10/25/06'
    u'%b %d %Y', u'%b %d, %Y',            # 'Oct 25 2006', 'Oct 25, 2006'
    u'%d %b %Y', u'%d %b, %Y',            # '25 Oct 2006', '25 Oct, 2006'
    u'%B %d %Y', u'%B %d, %Y',            # 'October 25 2006', 'October 25, 2006'
    u'%d %B %Y', u'%d %B, %Y',            # '25 October 2006', '25 October, 2006'
)

class DateField(CharField):
    def __init__(self, name='', value='', input_formats=None, js_calendar=True, *args, **kwargs):
        super(DateField, self).__init__(name, value, *args, **kwargs)
        self.input_formats = input_formats or DEFAULT_DATE_INPUT_FORMATS
        self.cssc = 'datefield'
        self.js_calendar = js_calendar
        if js_calendar:
#            self.media_files.append('/js/scw.js')
            self.media_files = ['/js/scw.js']
            self.onclick = 'scwShow(this,event);' 
        
    def clean(self):
        """
        Validates that the input can be converted to a date. Returns a Python
        datetime.date object.
        """
        super(DateField, self).clean()
        if self.is_empty():
            return None
        if isinstance(self.value, datetime.datetime):
            return self.value.date()
        if isinstance(self.value, datetime.date):
            return self.value
        for format in self.input_formats:
            try:
                return datetime.date(*time.strptime(self.value, format)[:3])
            except ValueError:
                continue
        raise ValidationError(_(u'Enter a valid date.'))
    
    def set_from_clean(self, value):
        date_format = self.input_formats[0]
        if value:
            self.value = value.strftime(str(date_format))
        else:
            value = None
            

DEFAULT_TIME_INPUT_FORMATS = (
    u'%H:%M:%S',     # '14:30:59'
    u'%H:%M',        # '14:30'
)

class TimeField(CharField):
    tattr_list = input.tattr_list
    def __init__(self, name='', value='', input_formats=None, *args, **kwargs):
        super(TimeField, self).__init__(name, value, *args, **kwargs)
        self.input_formats = input_formats or DEFAULT_TIME_INPUT_FORMATS

    def clean(self):
        """
        Validates that the input can be converted to a time. Returns a Python
        datetime.time object.
        """
        super(TimeField, self).clean()
        if self.is_empty():
            return None
        if isinstance(self.value, datetime.time):
            return self.value
        for format in self.input_formats:
            try:
                return datetime.time(*time.strptime(self.value, format)[3:6])
            except ValueError:
                continue
        raise ValidationError(_(u'Enter a valid time.'))

    def set_from_clean(self, value):
        time_format = self.input_formats[0]
        self.value = value.strftime(time_format)


DEFAULT_DATETIME_INPUT_FORMATS = (
    u'%Y-%m-%d %H:%M:%S',     # '2006-10-25 14:30:59'
    u'%Y-%m-%d %H:%M',        # '2006-10-25 14:30'
    u'%Y-%m-%d',              # '2006-10-25'
    u'%m/%d/%Y %H:%M:%S',     # '10/25/2006 14:30:59'
    u'%m/%d/%Y %H:%M',        # '10/25/2006 14:30'
    u'%m/%d/%Y',              # '10/25/2006'
    u'%m/%d/%y %H:%M:%S',     # '10/25/06 14:30:59'
    u'%m/%d/%y %H:%M',        # '10/25/06 14:30'
    u'%m/%d/%y',              # '10/25/06'
    u'%d.%m.%Y'               # '25.10.2007'
    u'%d.%m.%Y %H:%M'         # '25.10.2007 15:30'
    
)

class DateTimeField(Field):
    tattr_list = input.tattr_list
    def __init__(self, name='', value='', input_formats=None, *args, **kwargs):
        super(DateTimeField, self).__init__(name, value, *args, **kwargs)
        self.input_formats = input_formats or DEFAULT_DATETIME_INPUT_FORMATS

    def clean(self):
        """
        Validates that the input can be converted to a datetime. Returns a
        Python datetime.datetime object.
        """
        super(DateTimeField, self).clean()
        if self.is_empty():
            return None
        if isinstance(self.value, datetime.datetime):
            return self.value
        if isinstance(self.value, datetime.date):
            return datetime.datetime(self.value.year, self.value.month, self.value.day)
        for format in self.input_formats:
            try:
                return datetime.datetime(*time.strptime(self.value, format)[:6])
            except ValueError:
                continue
        raise ValidationError(_(u'Enter a valid date/time.'))

    def set_from_clean(self, value):
        datetime_format = self.input_formats[0]
        self.value = value.strftime(datetime_format)

class RegexField(CharField):
    def __init__(self, name, value, regex, max_length=None, min_length=None, error_message=None, *args, **kwargs):
        """
        regex can be either a string or a compiled regular expression object.
        error_message is an optional error message to use, if
        'Enter a valid value' is too generic for you.
        """
        super(RegexField, self).__init__(name, value, max_length, min_length, *args, **kwargs)
        if isinstance(regex, basestring):
            regex = re.compile(regex)
        self.regex = regex
        self.error_message = error_message or _(u'Enter a valid value.')

    def __deepcopy__(self, memo):
#        regex = self.regex
#        self.regex = None
#        __deepcopy__ = self.__deepcopy__
#        self.__deepcopy__ = None
#        result = deepcopy(self)
#        result.regex = regex
#        result.__deepcopy__ = __deepcopy__
#        return result
        result = self.__class__(self.name, self.value, self.regex, self.max_length, self.min_length, self.error_message)
        result.negation = self.negation
        result.required = self.required
        result.label = self.label
        result.initial = self.initial
        result.help_text = self.help_text
        memo[id(self)] = result 
        return result

    def clean(self):
        """
        Validates that the input matches the regular expression. Returns a
        Unicode object.
        """
        value = super(RegexField, self).clean()
        if value == u'':
            return value
        if not self.regex.search(value):
            raise ValidationError(self.error_message)
        return value

email_re = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"' # quoted-string
    r')@(?:[A-Z0-9-]+\.)+[A-Z]{2,6}$', re.IGNORECASE)  # domain

class EmailField(RegexField):
    def __init__(self, name='', value='', max_length=None, min_length=None, *args, **kwargs):
        super(EmailField, self).__init__(name, value, email_re, max_length, min_length,
            _(u'Enter a valid e-mail address.'), *args, **kwargs)
    def __deepcopy__(self, memo):
        result = self.__class__(self.name, self.value, self.max_length, self.min_length, self.error_message)
        result.negation = self.negation
        result.required = self.required
        result.label = self.label
        result.initial = self.initial
        result.help_text = self.help_text
        result.order = self.order
        memo[id(self)] = result 
        return result


class UploadedFile(types.StringType):
    "A wrapper for files uploaded in a FileField"
    def __init__(self, filename, content):
        self.filename = filename
        self.content = content

    def __unicode__(self):
        """
        The unicode representation is the filename, so that the pre-database-insertion
        logic can use UploadedFile objects
        """
        return self.filename

class FileField(Field):
    tattr_list = input.tattr_list
    def __init__(self, name='', value='', *args, **kwargs):
        super(FileField, self).__init__(name, value,  *args, **kwargs)

    def clean(self, data):
        super(FileField, self).clean(data)
        if not self.required and data in EMPTY_VALUES:
            return None
        try:
            f = UploadedFile(data['filename'], data['content'])
        except TypeError:
            raise ValidationError(_(u"No file was submitted. Check the encoding type on the form."))
        except KeyError:
            raise ValidationError(_(u"No file was submitted."))
        if not f.content:
            raise ValidationError(_(u"The submitted file is empty."))
        return f

class ImageField(FileField):
    def clean(self, data):
        """
        Checks that the file-upload field data contains a valid image (GIF, JPG,
        PNG, possibly others -- whatever the Python Imaging Library supports).
        """
        f = super(ImageField, self).clean(data)
        if f is None:
            return None
        from PIL import Image
        from cStringIO import StringIO
        try:
            # load() is the only method that can spot a truncated JPEG,
            #  but it cannot be called sanely after verify()
            trial_image = Image.open(StringIO(f.content))
            trial_image.load()
            # verify() is the only method that can spot a corrupt PNG,
            #  but it must be called immediately after the constructor
            trial_image = Image.open(StringIO(f.content))
            trial_image.verify()
        except Exception: # Python Imaging Library doesn't recognize it as an image
            raise ValidationError(_(u"Upload a valid image. The file you uploaded was either not an image or a corrupted image."))
        return f

url_re = re.compile(
    r'^https?://' # http:// or https://
    r'(?:(?:[A-Z0-9-]+\.)+[A-Z]{2,6}|' #domain...
    r'localhost|' #localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
    r'(?::\d+)?' # optional port
    r'(?:/?|/\S+)$', re.IGNORECASE)

class URLField(RegexField):
    def __init__(self, name='', value='', max_length=None, min_length=None, verify_exists=False,
            validator_user_agent=None, *args, **kwargs):
        super(URLField, self).__init__(name, value, url_re, max_length, min_length, _(u'Enter a valid URL.'), *args, **kwargs)
        self.verify_exists = verify_exists
        self.user_agent = validator_user_agent

    def clean(self):
        # If no URL scheme given, assume http://
        value = self.value
        if value and '://' not in value:
            value = u'http://%s' % value
        value = super(URLField, self).clean()
        if value == u'':
            return value
        if self.verify_exists:
            import urllib2
            from django.conf import settings
            headers = {
                "Accept": "text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5",
                "Accept-Language": "en-us,en;q=0.5",
                "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                "Connection": "close",
                "User-Agent": self.user_agent,
            }
            try:
                req = urllib2.Request(value, None, headers)
                u = urllib2.urlopen(req)
            except ValueError:
                raise ValidationError(_(u'Enter a valid URL.'))
            except: # urllib2.URLError, httplib.InvalidURL, etc.
                raise ValidationError(_(u'This URL appears to be a broken link.'))
        return value

class BooleanField(Field):
    tattr_list = input.tattr_list
    def __init__(self, name='', value=None, *args, **kwargs):
        super(BooleanField, self).__init__(name, value, *args, **kwargs)
        self.tag = self.tag or u'input'
        if self.tag == u'input':
            self.type = u'checkbox'
        self._value = 1
        self.checked = None
        self.tattr['value'] = 1
            
    def __setattr__(self, name, value):
        """
        Owerriden __setattr__ because value is field attribute and tag attribute and thus we cannot make it property, 
        because _setattr__ of WebWidget would just store it to tattr and wouldn't call _set_item method
        """
        if name == 'value':
            if (value is None) or (value == False):
                self.checked = None
            else:
                self.checked = 'checked'
        else:
            super(BooleanField, self).__setattr__(name, value)
    def __getattr__(self, name):
        if name == 'value':
            return self._value
        else:
            return super(BooleanField, self).__getattr__(name)

    def clean(self):
        "Returns a Python boolean object."
        return bool(self.checked)
    
    def _has_changed(self, initial, data):
        # Sometimes data or initial could be None or u'' which should be the
        # same thing as False.
        return bool(initial) != bool(data)

class HiddenField(CharField):
    is_hidden = True
    def __init__(self, name='', value='', *args, **kwargs):
        super(HiddenField, self).__init__(name, value, *args, **kwargs)
        if self.tag == u'input':
            self.type = u'hidden'


class HiddenDecimalField(DecimalField):
    is_hidden = True
    def __init__(self, name='', value='', max_value=None, min_value=None, max_digits=None, decimal_places=None, *args, **kwargs):
        super(HiddenDecimalField, self).__init__(name, value, max_value, min_value, max_digits, decimal_places, *args, **kwargs)
        if self.tag == u'input':
            self.type = u'hidden'
    



class ChoiceField(Field):
    #widget = Select
    tattr_list = select.tattr_list
    def __init__(self, name='', value='', choices=None, required=True, label=None, initial=None, help_text=None, *arg, **kwargs):
#        self._choices = None
#        self._value = None
        super(ChoiceField, self).__init__(name, value, required, label, initial, help_text, *arg, **kwargs)
        self.tag = 'select'

        if choices is None:
            self.choices = []
        else:
            self.choices = choices

    def make_content(self):
        self.content = []
        if self.choices:
            for value, caption in list(self.choices):
                if unicode(value) == unicode(self.value):
                    self.add(option(attr(value=value, selected='selected'), caption))
                else:
                    self.add(option(attr(value=value), caption))
                    
    def render(self, indent_level=0):
        self.make_content()
        return super(ChoiceField, self).render(indent_level)

#    def _get_choices(self):
#        return self._choices
#
#    def _set_choices(self, value):
#        self._choices = list(value)
#        self.regenerate_options_tags()
#    choices = property(_get_choices, _set_choices)
#    
#    def _get_value(self):
#        return self._value
#    
#    def _set_value(self, value):
#        self._value = value
#        self.regenerate_options_tags()
#    value = property(_get_value, _set_value)

    def clean(self):
        """
        Validates that the input is in self.choices.
        """
        value = super(ChoiceField, self).clean()
        if self.is_empty():
            value = u''
        if value == u'':
            return value
        valid_values = set([unicode(k) for k, v in self.choices])
        
        if value not in valid_values:
            raise ValidationError(_(u'Select a valid choice. That choice is not one of the available choices.'))
        return value
    
    def set_from_clean(self, value):
        self.value = unicode(value)

class NullBooleanField(ChoiceField):
    """
    A field whose valid values are None, True and False. Invalid values are
    cleaned to None.
    """
    def __init__(self, name='', value='',required=True, label=None, initial=None, help_text=None, *arg, **kwargs):
        choices = ((u'1', _('Unknown')), (u'2', _('Yes')), (u'3', ('No')))
        super(NullBooleanField, self).__init__(name, value, choices, required, label, initial, help_text, *arg, **kwargs)
        
    def clean(self):
        return {True: True, False: False}.get(self.value, None)
    
    def _has_changed(self, initial, data):
        # Sometimes data or initial could be None or u'' which should be the
        # same thing as False.
        return bool(initial) != bool(data)

class MultipleChoiceField(ChoiceField):
    def __init__(self, name='', value='', choices=None, required=True, label=None, initial=None, help_text=None, *args, **kwargs):
        super(MultipleChoiceField, self).__init__(name, value, choices, required, label, initial, help_text, *args, **kwargs)
        if self.tag == u'select':
            self.add(attr(multiple=u"multiple"))
   
    def make_content(self):
        self.content = []
        if self.choices:
            for value, caption in self.choices:
                if unicode(value) in self.value:
                    self.add(option(attr(value=value, selected='selected'), caption))
                else:
                    self.add(option(attr(value=value), caption))

    def clean(self):
        """
        Validates that the input is a list or tuple.
        """
        value = self.value
        if self.required and not value:
            raise ValidationError(_(u'This field is required.'))
        elif not self.required and not value:
            return []
        if not isinstance(value, (list, tuple)):
            value = list(value)
        # Validate that each value in the value list is in self.choices.
        valid_values = set([unicode(k) for k, v in self.choices])
        for val in value:
            if val not in valid_values:
                raise ValidationError(_(u'Select a valid choice. %s is not one of the available choices.') % val)
        return value
    
    def value_from_datadict(self, data):
#        debug('Jsem %s a beru si data %s' % (self.name, data.get(self.name, None)))
        value = data.get(self.name, None)
        if value is None:
            value = []
        if not isinstance(value, (list, tuple)):
            value = [value]
        return value
    
    def _has_changed(self, initial, data):
        if initial is None:
            initial = []
        if data is None:
            data = []
        if len(initial) != len(data):
            return True
        for value1, value2 in zip(initial, data):
            if unicode(value1) != unicode(value2):
                return True
        return False

class ComboField(Field):
    """
    A Field whose clean() method calls multiple Field clean() methods.
    """
    def __init__(self, name='', value='', fields=(), *args, **kwargs):
        super(ComboField, self).__init__(name, value, *args, **kwargs)
        # Set 'required' to False on the individual fields, because the
        # required validation will be handled by ComboField, not by those
        # individual fields.
        for f in fields:
            f.required = False
        self.fields = fields

    def clean(self):
        """
        Validates the given value against all of self.fields, which is a
        list of Field instances.
        """
        super(ComboField, self).clean()
        for field in self.fields:
            value = field.clean()
        return value
    

class MultiValueField(Field):
    """
    A Field that aggregates the logic of multiple Fields.

    Its clean() method takes a "decompressed" list of values, which are then
    cleaned into a single value according to self.fields. Each value in
    this list is cleaned by the corresponding field -- the first value is
    cleaned by the first field, the second value is cleaned by the second
    field, etc. Once all fields are cleaned, the list of clean values is
    "compressed" into a single value.

    Subclasses should not have to implement clean(). Instead, they must
    implement compress(), which takes a list of valid values and returns a
    "compressed" version of those values -- a single value.

    """
    tattr_list = span.tattr_list
    def __init__(self, name='', value='', fields=(), *args, **kwargs):
        
        # Set 'required' to False on the individual fields, because the
        # required validation will be handled by MultiValueField, not by those
        # individual fields.
        for field in fields:
            field.required = False
        self.fields = fields
        self._name = '' 
        super(MultiValueField, self).__init__(name, value, *args, **kwargs)
        self.tag = 'span'
        self.build_content()


    def _set_name(self, value):
        self._name = value
        for i, field in enumerate(self.fields):
            field.name = self._name + '/%d' % i
    def _get_name(self):
        return self._name
    name = property(_get_name, _set_name)
        
    def _set_value(self, value):
        if not value:
            self._value = [None] * len(self.fields)
            for field in self.fields:
                field.value = None
            return
        else:
            self._value = value
            if not isiterable(value) and len(value) != len(self.fields):
                raise TypeError(u'value of MultiField must be sequence with same length as number of fields in multifield (was %s)' % unicode(value))
            for i, val in enumerate(value):
                self.fields[i].value = val
    def _get_value(self):
        return self._value
    value = property(fget=lambda self: self._get_value(), fset=lambda self, value: self._set_value(value)) # late binding property

        
    def build_content(self):
        
        for field in self.fields:
            label_str = field.label or ''
            if label_str:
                label_str += ':'
            self.add(label_str, field)

    def clean(self):
        """
        Validates every value of self.fields.

        For example, if this MultiValueField was instantiated with
        fields=(DateField(), TimeField()), clean() would call
        DateField.clean() and TimeField.clean().
        """
        clean_data = []
        errors = ErrorList()

        for i, field in enumerate(self.fields):
            if self.required and field.is_required and field.is_empty():
                raise ValidationError(_(u'This field is required.'))
            try:
                clean_data.append(field.clean())
            except ValidationError, e:
                # Collect all validation errors in a single list, which we'll
                # raise at the end of clean(), rather than raising a single
                # exception for the first error we encounter.
                errors.extend(e.messages)
        if errors:
            raise ValidationError(errors)
        return self.compress(clean_data)

    def compress(self, data_list):
        """
        Returns a single value for the given list of values. The values can be
        assumed to be valid.

        For example, if this MultiValueField was instantiated with
        fields=(DateField(), TimeField()), this might return a datetime
        object created by combining the date and time in data_list.
        """
        raise NotImplementedError('Subclasses must implement this method.')

    def decompress(self, value):
        """
        Returns a list of decompressed values for the given compressed value.
        The given value can be assumed to be valid, but not necessarily
        non-empty.
        """
        raise NotImplementedError('Subclasses must implement this method.')

    def set_from_clean(self, value):
        val = self.decompress(value)
        self._value = val 
        if not isiterable(val) and len(val) != len(self.fields):
            raise TypeError(u'value of MultiField must be sequence with same length as number of fields in multifield (was %s)' % unicode(val))
        for i, v in enumerate(val):
            self.fields[i].set_from_clean(v)

    def value_from_datadict(self, data):
#        debug('beru data z %s k fieldum se jmeny %s' % (str(data), str([f.name for f in self.fields])))
        return [field.value_from_datadict(data) for field in self.fields]
    
    def is_empty(self):
        for field in self.fields:
            if not field.is_empty():
                return False
        return True
            
    def _has_changed(self, initial, data):
        if initial is None:
            initial = [u'' for x in range(0, len(data))]
        else:
            initial = self.decompress(initial)
        for field, initial, data in zip(self.fields, initial, data):
            if field._has_changed(initial, data):
                return True
        return False

class SplitDateTimeField(MultiValueField):
    def __init__(self, name='', value='', *args, **kwargs):
        fields = (DateField(), TimeField())
        super(SplitDateTimeField, self).__init__(name, value, fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list and data_list[0]:
            # Raise a validation error if time or date is empty
            # (possible if SplitDateTimeField has required=False).
            if data_list[0] in EMPTY_VALUES:
                raise ValidationError(_(u'Enter a valid date.'))
            if data_list[1] in EMPTY_VALUES:
                raise ValidationError(_(u'Enter a valid time.'))
            return datetime.datetime.combine(*data_list)
        return None

    def decompress(self, value):
        if value:
            import datetime
            t = value.time()
            the_time = datetime.time(t.hour,t.minute,t.second)
            return [value.date(), the_time]
        return [None, None]
    
    

ipv4_re = re.compile(r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$')

class IPAddressField(RegexField):
    def __init__(self, name='', value='', *args, **kwargs):
        super(IPAddressField, self).__init__(name, value, ipv4_re,
                            error_message=_(u'Enter a valid IPv4 address.'),
                            *args, **kwargs)

class SplitTimeField(MultiValueField):
    def __init__(self, name='', value='', *args, **kwargs):
        fields = (ChoiceField(choices=[[u'%d' % c, u'%02d' % c] for c in range(24)]), 
                  ChoiceField(choices=[[u'%d' % c, u'%02d' % c] for c in range(0, 60, 5)]))
        super(SplitTimeField, self).__init__(name, value, fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            return datetime.time(*[int(data) for data in data_list])
        return None

    def decompress(self, value):
        if value:
            return [value.hour, value.minute]
        return [u'0', u'0']
    
class SplitDateSplitTimeField(SplitDateTimeField):
    def __init__(self, name='', value='', *args, **kwargs): #  pylint: disable-msg=E1003 
        fields = (DateField(size=10), SplitTimeField())
        # Here is called really parent of parent of this class, to avoid self.fields initialization from parent:
        super(SplitDateTimeField, self).__init__(name, value, fields, *args, **kwargs) 

    def is_empty(self):
        return self.fields[0].is_empty()
    
    


