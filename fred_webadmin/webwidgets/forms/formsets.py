from logging import debug
import traceback

from forms import Form
from formsetlayouts import TableFormSetLayout
from fields import DecimalField, BooleanField, HiddenDecimalField
from fred_webadmin.webwidgets.utils import ErrorList, ValidationError
from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget

__all__ = ('BaseFormSet', 'all_valid')

# special field names
TOTAL_FORM_COUNT = 'TOTAL_FORMS'
INITIAL_FORM_COUNT = 'INITIAL_FORMS'
ORDERING_FIELD_NAME = 'ORDER'
DELETION_FIELD_NAME = 'DELETE'

class ManagementForm(Form):
    """
    ``ManagementForm`` is used to keep track of how many form instances
    are displayed on the page. If adding new forms via javascript, you should
    increment the count field of this form as well.
    """
    def __init__(self, *args, **kwargs):
        self.base_fields[TOTAL_FORM_COUNT] = HiddenDecimalField(name = TOTAL_FORM_COUNT)
        self.base_fields[INITIAL_FORM_COUNT] = HiddenDecimalField(name = INITIAL_FORM_COUNT)
        super(ManagementForm, self).__init__(*args, **kwargs)

class BaseFormSet(WebWidget):
    """
    A collection of instances of the same Form class.
    """
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
            initial=None, extra_count=1, error_class=ErrorList, is_nested=False, form_class=None, layout_class=TableFormSetLayout,
            can_order=False, can_delete=False, *content, **kwd):
        super(BaseFormSet, self).__init__(*content, **kwd)
        if not is_nested:
            self.tag = u'form'
        else:
            self.tag = u''
        self.is_bound = data is not None or files is not None
        self.prefix = prefix or 'form'
        self.auto_id = auto_id
        self.data = data
        self.files = files
        self.initial = initial
        self.extra_count = extra_count
        self.is_nested = is_nested
        self.error_class = error_class
        self.form_class = form_class
        self.layout_class = layout_class
        self.can_order = can_order
        self.can_delete = can_delete
        self._errors = None
        self._non_form_errors = None

        # initialization is different depending on whether we recieved data, initial, or nothing
        if data or files:
            self.management_form = ManagementForm(data, auto_id=self.auto_id, prefix=self.prefix, is_nested=True)
            if self.management_form.is_valid():
                self._total_form_count = self.management_form.cleaned_data[TOTAL_FORM_COUNT]
                self._initial_form_count = self.management_form.cleaned_data[INITIAL_FORM_COUNT]
            else:
                raise ValidationError('ManagementForm data is missing or has been tampered with')
        else:
            if initial:
                self._initial_form_count = len(initial)
                self._total_form_count = self._initial_form_count + self.extra_count
            else:
                self._initial_form_count = 0
                self._total_form_count = self.extra_count
            initial = {TOTAL_FORM_COUNT: self._total_form_count, INITIAL_FORM_COUNT: self._initial_form_count}
            self.management_form = ManagementForm(initial=initial, auto_id=self.auto_id, prefix=self.prefix)

        # instantiate all the forms and put them in self.forms
        self.forms = []
        for i in range(self._total_form_count):
            self.forms.append(self._construct_form(i))

    def __unicode__(self):
        return self.as_table()

    def _construct_form(self, i):
        """
        Instantiates and returns the i-th form instance in a formset.
        """
        kwargs = {'auto_id': self.auto_id, 'prefix': self.add_prefix(i), 'is_nested': True}
        if self.data or self.files:
            kwargs['data'] = self.data
            kwargs['files'] = self.files
        if self.initial:
            try:
                kwargs['initial'] = self.initial[i]
            except IndexError:
                pass
        # Allow extra forms to be empty.
        if i >= self._initial_form_count:
            kwargs['empty_permitted'] = True
        form = self.form_class(**kwargs)
        self.add_fields(form, i)
        form.set_fields_values() # to set values of deleted fields
        return form

    def _get_initial_forms(self):
        """Return a list of all the intial forms in this formset."""
        return self.forms[:self._initial_form_count]
    initial_forms = property(_get_initial_forms)

    def _get_extra_forms(self):
        """Return a list of all the extra forms in this formset."""
        return self.forms[self._initial_form_count:]
    extra_forms = property(_get_extra_forms)

    # Maybe this should just go away?
    def _get_cleaned_data(self):
        """
        Returns a list of form.cleaned_data dicts for every form in self.forms.
        """
        try:
            if not self.is_valid():
                raise AttributeError("'%s' object has no attribute 'cleaned_data'" % self.__class__.__name__)
            cleaned_data_list = []
            for form in self.forms:
                if form.cleaned_data is not None and not form.cleaned_data.get(DELETION_FIELD_NAME):
#                    Problem: DELETION FIELD je furt False!!! 
                    data = dict(form.cleaned_data)
                    if data.has_key(DELETION_FIELD_NAME):
                        if not data[DELETION_FIELD_NAME]: # deletion checkbox wasn't checked, just get rid of deletion field in actual data
                            data.pop(DELETION_FIELD_NAME)
                            cleaned_data_list.append(data)
                        else:
                            debug('Form %s was marked for deletion, and so it is not include to formsets cleaned_data' % form)
            return cleaned_data_list
        except AttributeError:
            raise RuntimeError('Camouflaged AttributeError from _get_cleaned_data of formset, original error: \n %s' % unicode(traceback.format_exc()))
         
    cleaned_data = property(_get_cleaned_data)

    def _get_deleted_forms(self):
        """
        Returns a list of forms that have been marked for deletion. Raises an 
        AttributeError is deletion is not allowed.
        """
        if not self.is_valid() or not self.can_delete:
            raise AttributeError("'%s' object has no attribute 'deleted_forms'" % self.__class__.__name__)
        # construct _deleted_form_indexes which is just a list of form indexes
        # that have had their deletion widget set to True
        if not hasattr(self, '_deleted_form_indexes'):
            self._deleted_form_indexes = []
            for i in range(0, self._total_form_count):
                form = self.forms[i]
                # if this is an extra form and hasn't changed, don't consider it
                if i >= self._initial_form_count and not form.has_changed():
                    continue
                if form.cleaned_data[DELETION_FIELD_NAME]:
                    self._deleted_form_indexes.append(i)
        return [self.forms[i] for i in self._deleted_form_indexes]
    deleted_forms = property(_get_deleted_forms)

    def _get_ordered_forms(self):
        """
        Returns a list of form in the order specified by the incoming data.
        Raises an AttributeError is deletion is not allowed.
        """
        if not self.is_valid() or not self.can_order:
            raise AttributeError("'%s' object has no attribute 'ordered_forms'" % self.__class__.__name__)
        # Construct _ordering, which is a list of (form_index, order_field_value)
        # tuples. After constructing this list, we'll sort it by order_field_value
        # so we have a way to get to the form indexes in the order specified
        # by the form data.
        if not hasattr(self, '_ordering'):
            self._ordering = []
            for i in range(0, self._total_form_count):
                form = self.forms[i]
                # if this is an extra form and hasn't changed, don't consider it
                if i >= self._initial_form_count and not form.has_changed():
                    continue
                # don't add data marked for deletion to self.ordered_data
                if self.can_delete and form.cleaned_data[DELETION_FIELD_NAME]:
                    continue
                # A sort function to order things numerically ascending, but
                # None should be sorted below anything else. Allowing None as
                # a comparison value makes it so we can leave ordering fields
                # blamk.
                def compare_ordering_values(x, y):
                    if x[1] is None:
                        return 1
                    if y[1] is None:
                        return -1
                    return x[1] - y[1]
                self._ordering.append((i, form.cleaned_data[ORDERING_FIELD_NAME]))
            # After we're done populating self._ordering, sort it.
            self._ordering.sort(compare_ordering_values)
        # Return a list of form.cleaned_data dicts in the order spcified by
        # the form data.
        return [self.forms[i[0]] for i in self._ordering]
    ordered_forms = property(_get_ordered_forms)

    def non_form_errors(self):
        """
        Returns an ErrorList of errors that aren't associated with a particular
        form -- i.e., from formset.clean(). Returns an empty ErrorList if there
        are none.
        """
        if self._non_form_errors is not None:
            return self._non_form_errors
        return self.error_class()

    def _get_errors(self):
        """
        Returns a list of form.errors for every form in self.forms.
        """
        if self._errors is None:
            self.full_clean()
        return self._errors
    errors = property(_get_errors)

    def is_valid(self):
        """
        Returns True if form.errors is empty for every form in self.forms.
        """

        if not self.is_bound:
            return False
        
        # We loop over every form.errors here rather than short circuiting on the
        # first failure to make sure validation gets triggered for every form.
        forms_valid = True
        for errors in self.errors:
            if bool(errors):
                forms_valid = False
        return forms_valid and not bool(self.non_form_errors())

    def full_clean(self):
        """
        Cleans all of self.data and populates self._errors.
        """
        self._errors = []
        if not self.is_bound: # Stop further processing.
            return
        for i in range(0, self._total_form_count):
            form = self.forms[i]
            self._errors.append(form.errors)
        # Give self.clean() a chance to do cross-form validation.
        try:
            self.clean()
        except ValidationError, e:
            self._non_form_errors = e.messages

    def clean(self):
        """
        Hook for doing any extra formset-wide cleaning after Form.clean() has
        been called on every form. Any ValidationError raised by this method
        will not be associated with a particular form; it will be accesible
        via formset.non_form_errors()
        """
        pass

    def add_fields(self, form, index):
        """A hook for adding extra fields on to each form instance."""
        if self.can_order:
            # Only pre-fill the ordering field for initial forms.
            if index < self._initial_form_count:
                form.fields[ORDERING_FIELD_NAME] = DecimalField(ORDERING_FIELD_NAME, label='Order', initial=index+1, required=False)
            else:
                form.fields[ORDERING_FIELD_NAME] = DecimalField(ORDERING_FIELD_NAME, label='Order', required=False)
        if self.can_delete:
            form.fields[DELETION_FIELD_NAME] = BooleanField(form.add_prefix(DELETION_FIELD_NAME), label='Delete', required=False, title='unchecked')

    def add_prefix(self, index):
        return '%s-%s' % (self.prefix, index)

    def is_multipart(self):
        """
        Returns True if the formset needs to be multipart-encrypted, i.e. it
        has FileInput. Otherwise, False.
        """
        return self.forms[0].is_multipart()

    def render(self, indent_level=0):
        debug('RENDERING of %s indent_level %s' % (self.__class__.__name__, indent_level))
        
        self.content = [] # empty previous content (if render would be called moretimes, there would be multiple forms instead one )
        debug('Adding layout %s to %s' % (self.layout_class, self.__class__.__name__))
        self.add(self.layout_class(self))
        debug('After adding layout %s to %s' % (self.layout_class, self.__class__.__name__))
        return super(BaseFormSet, self).render(indent_level)

# XXX: This API *will* change. Use at your own risk.
def _formset_factory(form, formset=BaseFormSet, extra_count=1, can_order=False, can_delete=False):
    """Return a FormSet for the given form class."""
    attrs = {'form': form, 'extra_count': extra_count, 'can_order': can_order, 'can_delete': can_delete}
    return type(form.__name__ + 'FormSet', (formset,), attrs)

#def all_valid(formsets):
#    """Returns true if every formset in formsets is valid."""
#    valid = True
#    for formset in formsets:
#        if not formset.is_valid():
#            valid = False
#    return valid
