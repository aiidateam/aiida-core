from aida.common import aidalogger
from aida.common.exceptions import ValidationError

## TODO: see if we want to have a function to rebuild a nested dictionary as
## a nested AttributeDict object when deserializing with json.
## (now it deserialized to a standard dictionary; comparison of
## AttributeDict == dict works fine, though.
## Note also that when pickling, instead, the structure is well preserved)

## Note that for instance putting this code in __getattr__ doesn't work:
## everytime I try to write on a.b.c I am actually writing on a copy
##    return AttributeDict(item) if type(item) == dict else item

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
    A dictionary with access to the keys as attributes, and with filtering of valid
    attributes. This is only the base class, without valid attributes;
    use a derived class to do the actual work.
    E.g.:
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
    A dictionary with access to the keys as attributes, and with an internal value
    storing the 'default' keys to be distinguished from extra fields.
    
    Extra methods defaultkeys() and extrakeys() divide the set returned by keys()
    in default keys (i.e. those defined at definition time) and other keys.
    There is also a method get_default_fields() to return the internal list.
    
    Moreover, for undefined default keys, it returns None instead of raising a
    KeyError/AttributeError exception.

    Define the _default_fields in a subclass!    
    E.g.:
    class TestExample(DefaultFieldsAttributeDict):
        _default_fields = ('a','b','c')
    
    When the validate() method is called, it calls in turn all validate_KEY
    methods, where KEY is one of the default keys.
    If the method is not present, the field is considered to be always valid.
    Each validate_KEY method should accept a single argument 'value' that will
    contain the value to be checked.
    It raises a ValidationError if any of the validate_KEY
    function raises an exception, otherwise it simply returns.
    NOTE: the validate_ functions are called also for unset fields, so if the
    field can be empty on validation, you have to start your validation
    function with something similar to
    if value is None:
        return

    TODO: decide behavior if I set to None a field. Current behavior, if
        a is an instanec and 'def_field' one of the default fields, that is 
        undefined, we get:
           a.get('def_field') -> None
           a.get('def_field','whatever') -> 'whatever'
           a.defaultkeys() does NOT contain 'def_field'

       if we do a.def_field = None, then the behavior becomes
           a.get('def_field') -> None
           a.get('def_field','whatever') -> None
           a.defaultkeys() DOES contain 'def_field'

       See if we want that setting a default field to None means deleting it.
    """
    _default_fields = tuple()

    def validate(self):
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

if __name__ == "__main__":
    import unittest
    import copy

    class TestFFADExample(FixedFieldsAttributeDict):
        """
        An example class that accepts only the 'a', 'b' and 'c' keys/attributes.
        """
        _valid_fields = ('a','b','c')


    class TestDFADExample(DefaultFieldsAttributeDict):
        """
        An example class that has 'a', 'b' and 'c' as default keys.
        """
        _default_fields = ('a','b','c')

        def validate_a(self,value):
            # Ok if unset
            if value is None:
                return
            
            if not isinstance(value,int):
                raise TypeError('expecting integer')
            if value < 0:
                raise ValueError('expecting a positive or zero value')
        

    class TestAttributeDictAccess(unittest.TestCase):
        """
        Try to access the dictionary elements in various ways, copying (shallow and
        deep), check raised exceptions.
        """

        def test_access_dict_to_attr(self):
            d = AttributeDict()
            d['test'] = 'abc'
            self.assertEquals(d.test, 'abc')

        def test_access_attr_to_dict(self):
            d = AttributeDict()
            d.test = 'def'
            self.assertEquals(d['test'], 'def')
   
        def test_access_nonexisting_asattr(self):
            d = AttributeDict()
            with self.assertRaises(AttributeError):
                a = d.test

        def test_access_nonexisting_askey(self):
            d = AttributeDict()
            with self.assertRaises(KeyError):
                a = d['test']

        def test_del_nonexisting_askey(self):
            d = AttributeDict()
            with self.assertRaises(KeyError):
                del d['test']

        def test_del_nonexisting_asattr(self):
            d = AttributeDict()
            with self.assertRaises(AttributeError):
                del d.test
                
        def test_copy(self):
            d1 = AttributeDict()
            d1.x = 'a'
            d2 = d1.copy()
            d2.x = 'b'
            self.assertEquals(d1.x, 'a')
            self.assertEquals(d2.x, 'b')

        def test_delete_after_copy(self):
            d1 = AttributeDict()
            d1.x = 'a'
            d1.y = 'b'
            d2 = d1.copy()
            del d1.x
            del d1['y']
            with self.assertRaises(AttributeError):
                _ = d1.x
            with self.assertRaises(KeyError):
                _ = d1['y']
            self.assertEquals(d2['x'], 'a')
            self.assertEquals(d2.y, 'b')
            self.assertEquals(set(d1.keys()), set({}))
            self.assertEquals(set(d2.keys()), set({'x', 'y'}))
            
        def test_shallowcopy1(self):
            d1 = AttributeDict()
            d1.x = [1,2,3]
            d1.y = 3
            d2 = d1.copy()
            d2.x[0] = 4
            d2.y = 5
            self.assertEquals(d1.x, [4,2,3]) # copy does a shallow copy
            self.assertEquals(d2.x, [4,2,3])
            self.assertEquals(d1.y,3)
            self.assertEquals(d2.y,5)

        def test_shallowcopy2(self):
            """
            Also test access at nested levels
            """
            d1 = AttributeDict()
            d1.x = {'a': 'b', 'c': 'd'}
#            d2 = copy.deepcopy(d1)
            d2 = d1.copy()
            # doesn't work like this, would work as d2['x']['a']
            # i think that it is because deepcopy on dict actually creates a
            # copy only if the data is changed; but for a nested dict,
            # d2.x returns a dict wrapped in our class and this looses all the
            # information on what should be updated when changed.
            d2.x['a'] = 'ggg'
            self.assertEquals(d1.x['a'], 'ggg') # copy does a shallow copy
            self.assertEquals(d2.x['a'], 'ggg')

        def test_deepcopy1(self):
            d1 = AttributeDict()
            d1.x = [1,2,3]
            d2 = copy.deepcopy(d1)
            d2.x[0] = 4
            self.assertEquals(d1.x, [1,2,3]) 
            self.assertEquals(d2.x, [4,2,3])

        def test_shallowcopy2(self):
            """
            Also test access at nested levels
            """
            d1 = AttributeDict()
            d1.x = {'a': 'b', 'c': 'd'}
            d2 = copy.deepcopy(d1)
            d2.x['a'] = 'ggg'
            self.assertEquals(d1.x['a'], 'b') # copy does a shallow copy
            self.assertEquals(d2.x['a'], 'ggg')   

    class TestAttributeDictNested(unittest.TestCase):
        """
        Test the functionality of nested AttributeDict classes.
        """
        
        def test_nested(self):
            d1 = AttributeDict({'x':1,'y':2})
            d2 = AttributeDict({'z':3,'w':4})
            d1.nested = d2
            self.assertEquals(d1.nested.z, 3)
            self.assertEquals(d1['nested'].w, 4)
            self.assertEquals(d1.nested['w'],4)
            d2['w'] = 5
            self.assertEquals(d1['nested'].w, 5)
            self.assertEquals(d1.nested['w'],5)
            
        def test_comparison(self):
            d1 = AttributeDict({'x':1,'y':2, 'z': AttributeDict({'w': 3})})
            d2 = AttributeDict({'x':1,'y':2, 'z': AttributeDict({'w': 3})})

            # They compare to the same value but they are different objects
            self.assertFalse(d1 is d2)
            self.assertEquals(d1, d2)
            
            d2.z.w = 4
            self.assertNotEquals(d1, d2)
        
        def test_nested_deepcopy(self):
            d1 = AttributeDict({'x':1,'y':2})
            d2 = AttributeDict({'z':3,'w':4})
            d1.nested = d2
            d1copy = copy.deepcopy(d1)
            self.assertEquals(d1copy.nested.z, 3)
            self.assertEquals(d1copy['nested'].w, 4)
            self.assertEquals(d1copy.nested['w'],4)
            d2['w'] = 5
            self.assertEquals(d1copy['nested'].w, 4) # Nothing has changed
            self.assertEquals(d1copy.nested['w'],4)  # Nothing has changed
            self.assertEquals(d1copy.nested.w,4)     # Nothing has changed
            
            self.assertEquals(d1['nested'].w, 5) # The old one is updated
            self.assertEquals(d1.nested['w'],5)  # The old one is updated
            self.assertEquals(d1.nested.w,5)     # The old one is updated
            
            d1copy.nested.w = 6
            self.assertEquals(d1copy.nested.w,6)
            self.assertEquals(d1.nested.w,5)
            self.assertEquals(d2.w,5)

    class TestAttributeDictSerialize(unittest.TestCase):
        """
        Test serialization/deserialization (with json, pickle, ...)
        """
        def test_json(self):
            import json
            d1 = AttributeDict({'x':1,'y':2})
            d2 = json.loads(json.dumps(d1))
            # Note that here I am comparing a dictionary (d2) with a 
            # AttributeDict (d2) and they still compare to equal
            self.assertEquals(d1, d2)

        def test_json_recursive(self):
            import json
            d1 = AttributeDict({'x':1,'y':2,'z': AttributeDict({'w': 4})})
            d2 = json.loads(json.dumps(d1))
            # Note that here I am comparing a dictionary (d2) with a (recursive)
            # AttributeDict (d2) and they still compare to equal
            self.assertEquals(d1, d2)
        
        def test_pickle(self):
            import pickle
            d1 = AttributeDict({'x':1,'y':2})
            d2 = pickle.loads(pickle.dumps(d1))
            self.assertEquals(d1, d2)
            
        def test_pickle_recursive(self):
            import pickle
            d1 = AttributeDict({'x':1,'y':2,'z': AttributeDict({'w': 4})})
            d2 = pickle.loads(pickle.dumps(d1))
            self.assertEquals(d1, d2)
   
    class TestFFAD(unittest.TestCase):
        
        def test_insertion(self):
            a = TestFFADExample()
            a['a'] = 1
            a.b = 2
            # Not a valid key.
            with self.assertRaises(ValueError):
                a['d'] = 2
            with self.assertRaises(ValueError):
                a.e = 5

        def test_insertion_on_init(self):
            a = TestFFADExample({'a':1, 'b': 2})
            with self.assertRaises(ValueError):
                # 'd' is not a valid key
                a = TestFFADExample({'a':1, 'd': 2})
        
        def test_pickle(self):
            """
            Note: pickle works here because self._valid_fields is defined
            at the class level!
            """
            import pickle
            a = TestFFADExample({'a':1, 'b': 2})
            b = pickle.loads(pickle.dumps(a))
            b.c = 3
            with self.assertRaises(ValueError):
                b['d'] = 2
        
        def test_class_attribute(self):
            """
            I test that the get_valid_fields() is working as a class method,
            so I don't need to instantiate the class to get the list.
            """
            self.assertEquals(set(TestFFADExample.get_valid_fields()),
                              set(['a','b','c']))
   
    class TestDFAD(unittest.TestCase):
        
        def test_insertion_and_retrieval(self):
            a = TestDFADExample()
            a['a'] = 1
            a.b = 2
            a['d'] = 3
            a.e = 4
            self.assertEquals(a.a,1)
            self.assertEquals(a.b,2)
            self.assertEquals(a['d'],3)
            self.assertEquals(a['e'],4)
            
        def test_keylist_method(self):
            a = TestDFADExample()
            a['a'] = 1
            a.b = 2
            a['d'] = 3
            a.e = 4

            self.assertEquals(set(a.get_default_fields()),set(['a','b','c']))
            self.assertEquals(set(a.keys()),set(['a','b','d','e']))
            self.assertEquals(set(a.defaultkeys()),set(['a','b']))
            self.assertEquals(set(a.extrakeys()),set(['d','e']))
            self.assertIsNone(a.c)
        
        def test_class_attribute(self):
            """
            I test that the get_default_fields() is working as a class method,
            so I don't need to instantiate the class to get the list.
            """
            self.assertEquals(set(TestDFADExample.get_default_fields()),
                              set(['a','b','c']))


        def test_validation(self):
            o = TestDFADExample()

            # Should be ok to have an empty 'a' attribute
            o.validate()
            
            o.a = 4
            o.b = 'text'

            # This should be fine
            o.validate()

            o.a = 'string'
            # o.a must be a positive integer
            with self.assertRaises(ValidationError):
                o.validate()
   
            o.a = -3
            # a.a must be a positive integer
            with self.assertRaises(ValidationError):
                o.validate()

    import logging
    aidalogger.setLevel(logging.DEBUG)
    
    unittest.main()
