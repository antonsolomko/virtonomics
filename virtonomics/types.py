class List(list):
    """Extends built-in list. Values are assumed to be dictionaries.
    
    Callable. When called with keyword arguments, return the list of 
    dictionaries that contain all the passed key-value pairs.
    If a list or a tuple is passed as a keyword argument, perform inclusion
    test for the corresponding values.
    If the resulting list contains a unique element, this single dictionary 
    can be extracted using select method with the same arguments.
    """
    
    def __call__(self, **filters):
        for fk, fv in filters.items():
            if not (isinstance(fv, list) or isinstance(fv, tuple) or isinstance(fv, set)):
                filters[fk] = [fv]
        return List(v for v in self if all(v.get(fk) in fv for fk, fv in filters.items()))
    
    def select(self, **filters):
        """Return the unique dictionary that contains passed key-value pairs.
        If not unique or does not exist, return None.
        """
        result = self(**filters)
        if len(result) == 1:
            return result[0]
        else:
            return None


class Dict(dict):
    """Extends built-in dict. Values are assumed to be dictionaries.
    
    Callable. When called with keyword arguments, return the dictionaries
    that contain all the passed key-value pairs.
    If a list or a tuple is passed as a keyword argument, perform inclusion
    test for the corresponding values.
    If the resulting dictionary contains a unique element, this single 
    dictionary can be extracted using select method with the same arguments.
    """
    
    def __call__(self, **filters):
        for fk, fv in filters.items():
            if not (isinstance(fv, list) or isinstance(fv, tuple) or isinstance(fv, set)):
                filters[fk] = [fv]
        return Dict({k: v for k, v in self.items()
                     if all(v.get(fk) in fv for fk, fv in filters.items())})
    
    def select(self, **filters):
        """Return the unique dictionary that contains passed key-value pairs.
        If not unique or does not exist, return None.
        """
        result = self(**filters)
        if len(result) == 1:
            return next(iter(result.values()))
        else:
            return None