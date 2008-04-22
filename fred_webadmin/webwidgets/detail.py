class DeclarativeDFieldsMetaclass(WebWidget.__metaclass__):
    """
    Metaclass that converts Field attributes to a dictionary called
    'base_fields', taking into account parent class 'base_fields' as well.
    """
    def __new__(cls, name, bases, attrs):
        fields = [(field_name, attrs.pop(field_name)) for field_name, obj in attrs.items() if isinstance(obj, Field)]
        fields.sort(lambda x, y: cmp(x[1].creation_counter, y[1].creation_counter))

        # If this class is subclassing another Form, add that Form's fields.
        # Note that we loop over the bases in *reverse*. This is necessary in
        # order to preserve the correct order of fields.
        print cls, '|',  name, '|', bases, '|', attrs

        for base in bases[::-1]:
            if hasattr(base, 'base_fields'):
                fields = base.base_fields.items() + fields

        attrs['base_fields'] = SortedDictFromList(fields)
        for i, (field_name, field) in enumerate(attrs['base_fields'].items()):
            field.name = field_name
            field.order = i

        new_class = type.__new__(cls, name, bases, attrs)
        return new_class
    
