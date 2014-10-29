# -*- coding: utf-8 -*-
from aiida.common import aiidalogger
from aiida.common.exceptions import ValidationError

## TODO: see if we want to have a function to rebuild a nested dictionary as
## a nested AttributeDict object when deserializing with json.
## (now it deserialized to a standard dictionary; comparison of
## AttributeDict == dict works fine, though.
## Note also that when pickling, instead, the structure is well preserved)

## Note that for instance putting this code in __getattr__ doesn't work:
## everytime I try to write on a.b.c I am actually writing on a copy
##    return AttributeDict(item) if type(item) == dict else item

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class Enumerate(frozenset):
    def __getattr__(self,name):
        if name in self:
            return name
        raise AttributeError("No attribute '{}' in Enumerate '{}'".format(
                name, self.__class__.__name__))

    def __setattr__(self, name, value):
        raise AttributeError("Cannot set attribute in Enumerate '{}'".format(
                self.__class__.__name__))

    def __delattr__(self, name):
        raise AttributeError("Cannot delete attribute in Enumerate '{}'".format(
                self.__class__.__name__))

class AttributeDict(dict):
    """
    This class internally stores values in a dictionary, but exposes
    the keys also as attributes, i.e. asking for
    attrdict.key
    will return the value of attrdict['key'] and so on.

    Raises an AttributeError if the key does not exist, when called as an attribute,
    while the usual KeyError if the key does not exist and the dictionary syntax is
    used.
    """
    def __init__(self, init={}):
        """
        Possibly set the initial values of the dictionary from an external dictionary
        init. Note that the attribute-calling syntax will work only 1 level deep.
        """
        dict.__init__(self, init)

    def __repr__(self):
        """
        Representation of the object.
        """
        return "%s(%s)" % (self.__class__.__name__, dict.__repr__(self))

    def __getattr__(self, attr):
        """
        Read a key as an attribute. Raise AttributeError on missing key.
        Called only for attributes that do not exist.
        """
        try:
            return self[attr]
        except KeyError:
            errmsg = "'{}' object has no attribute '{}'".format(
                self.__class__.__name__, attr)
            raise AttributeError(errmsg)

    def __setattr__(self, attr, value):
        """
        Set a key as an attribute. 
        """
        self[attr] = value

    def __delattr__(self, attr):
        """
        Delete a key as an attribute. Raise AttributeError on missing key.
        """
        try:
            del self[attr]
        except KeyError:
            errmsg = "'{}' object has no attribute '{}'".format(
                self.__class__.__name__, attr)
            raise AttributeError(errmsg)

    def copy(self):
        """
        Shallow copy.
        """
        return self.__class__(self)

    def __deepcopy__(self, memo={}):
        """
        Support deepcopy.
        """
        from copy import deepcopy
        retval = deepcopy(dict(self))
        return self.__class__(retval)

    def __getstate__(self): 
        """
        Needed for pickling this class.
        """
        return self.__dict__.copy() 

    def __setstate__(self,dict): 
        """
        Needed for pickling this class.
        """
        self.__dict__.update(dict) 

class FixedFieldsAttributeDict(AttributeDict):
    """
    A dictionary with access to the keys as attributes, and with filtering
    of valid attributes. 
    This is only the base class, without valid attributes;
    use a derived class to do the actual work.
    E.g.::

        class TestExample(FixedFieldsAttributeDict):
            _valid_fields = ('a','b','c')
    """
    _valid_fields = tuple()
    def __init__(self,init={}):
        for key in init:
            if key not in self._valid_fields:
                errmsg = "'{}' is not a valid key for object '{}'".format(
                    key, self.__class__.__name__)
                raise ValueError(errmsg)
        super(FixedFieldsAttributeDict, self).__init__(init)

    def __setitem__(self, item, value):
        """
        Set a key as an attribute. 
        """
        if item not in self._valid_fields:
            errmsg = "'{}' is not a valid key for object '{}'".format(
                item, self.__class__.__name__)
            raise ValueError(errmsg)
        super(FixedFieldsAttributeDict,self).__setitem__(item, value)

    def __setattr__(self, attr, value):
        """
        Overridden to allow direct access to fields with underscore.
        """
        if attr.startswith('_'):
            object.__setattr__(self,attr,value)
        else:
            super(FixedFieldsAttributeDict,self).__setattr__(attr,value)
            
    @classmethod
    def get_valid_fields(cls):
        """
        Return the list of valid fields.
        """
        return cls._valid_fields


class DefaultFieldsAttributeDict(AttributeDict):
    """
    A dictionary with access to the keys as attributes, and with an
    internal value storing the 'default' keys to be distinguished
    from extra fields.
    
    Extra methods defaultkeys() and extrakeys() divide the set returned by
    keys() in default keys (i.e. those defined at definition time)
    and other keys.
    There is also a method get_default_fields() to return the internal list.
    
    Moreover, for undefined default keys, it returns None instead of raising a
    KeyError/AttributeError exception.

    Remember to define the _default_fields in a subclass!    
    E.g.::
        
        class TestExample(DefaultFieldsAttributeDict):
            _default_fields = ('a','b','c')
    
    When the validate() method is called, it calls in turn all validate_KEY
    methods, where KEY is one of the default keys.
    If the method is not present, the field is considered to be always valid.
    Each validate_KEY method should accept a single argument 'value' that will
    contain the value to be checked.

    It raises a ValidationError if any of the validate_KEY
    function raises an exception, otherwise it simply returns.
    NOTE: the validate\_ functions are called also for unset fields, so if the
    field can be empty on validation, you have to start your validation
    function with something similar to::

        if value is None:
            return

    .. todo:: 
        Decide behavior if I set to None a field.
        Current behavior, if
        ``a`` is an instance and 'def_field' one of the default fields, that is 
        undefined, we get:
        
        * ``a.get('def_field')``: None
        * ``a.get('def_field','whatever')``: 'whatever'
        * Note that ``a.defaultkeys()`` does NOT contain 'def_field'

        if we do ``a.def_field = None``, then the behavior becomes
 
        * ``a.get('def_field')``: None
        * ``a.get('def_field','whatever')``: None
        * Note that ``a.defaultkeys()`` DOES contain 'def_field'

        See if we want that setting a default field to None means deleting it.
    """
    _default_fields = tuple()

    def validate(self):
        """
        Validate the keys, if any ``validate_*`` method is available.
        """
        for key in self.get_default_fields():
            # I get the attribute starting with validate_ and containing the name of the key
            # I set a dummy function if there is no validate_KEY function defined
            validator = getattr(self,'validate_{}'.format(key), lambda value: None)
            if callable(validator):
                try:
                    validator(self[key])
                except Exception as e:
                    raise ValidationError("Invalid value for key '{}' [{}]: {}".format(
                        key, e.__class__.__name__, e.message))

    def __setattr__(self, attr, value):
        """
        Overridden to allow direct access to fields with underscore.
        """
        if attr.startswith('_'):
            object.__setattr__(self,attr,value)
        else:
            super(DefaultFieldsAttributeDict,self).__setattr__(attr,value)
    
    def __getitem__(self,key):
        """
        Return None instead of raising an exception if the key does not exist
        but is in the list of default fields.
        """
        try:
            return super(DefaultFieldsAttributeDict,self).__getitem__(key)
        except KeyError:
            if key in self._default_fields:
                return None
            else:
                raise

    @classmethod
    def get_default_fields(cls):
        """
        Return the list of default fields, either defined in the instance or not.
        """
        return list(cls._default_fields)
    
    def defaultkeys(self):
        """
        Return the default keys defined in the instance.
        """
        return [_ for _ in self.keys() if _ in self._default_fields]
        
    def extrakeys(self):
        """
        Return the extra keys defined in the instance.
        """
        return [_ for _ in self.keys() if _ not in self._default_fields]

