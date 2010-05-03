class FilterFormEmptyValue(object):
    ''' Class used in clean method of Field as empty value (if
        field.is_emtpy()=True, than clean vill return instance of this object.
    '''
    pass
