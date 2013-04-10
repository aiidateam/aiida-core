import cPickle

from aida.common import aidalogger

## TODO: when a KeyError is raised accessing an Attribute, the corresponding
##       AttributeError should be rised instead; corrects tests and code
## TODO: see if we want to have a function to rebuild a nested dictionary as a nested
##       AttributeDict object when deserializing with json
#        Note that for instance putting this code in __getattr__ doesn't work:
#        everytime I try to write on a.b.c I am actually writing on a copy
#          return AttributeDict(item) if type(item) == dict else item

class AttributeDict(dict):
    """
    This class internally stores values in a dictionary, but exposes
    the keys also as attributes, i.e. asking for
    attrdict.key
    will return the value of attrdict['key'] and so on.

    Raises a KeyError if the key does not exist, even if called as an attribute.
    """
    def __init__(self, init={}):
        dict.__init__(self, init)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, dict.__repr__(self))

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            errmsg = "'{}' object has no attribute '{}'".format(
                self.__class__.__name__, attr)
            raise AttributeError(errmsg)

    def __setattr__(self, attr, value):
        self[attr] = value

    def __delattr__(self, attr):
        try:
            del self[attr]
        except KeyError:
            errmsg = "'{}' object has no attribute '{}'".format(
                self.__class__.__name__, attr)
            raise AttributeError(errmsg)

    def copy(self):
        return self.__class__(self)

    def __deepcopy__(self, memo={}):
        from copy import deepcopy
        retval = deepcopy(dict(self))
        return self.__class__(retval)

    def __getstate__(self): 
        ''' Needed for pickling '''
        return self.__dict__.copy() 

    def __setstate__(self,dict): 
        ''' Needed for pickling '''
        self.__dict__.update(dict) 

if __name__ == "__main__":
    import unittest
    import copy


    class TestAccess(unittest.TestCase):
        """
        Try to access the dictionary elements in various ways
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
            d2 = d1.copy()
            d2.x[0] = 4
            self.assertEquals(d1.x, [4,2,3]) # copy does a shallow copy
            self.assertEquals(d2.x, [4,2,3])

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

    class TestNested(unittest.TestCase):
        
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

    class TestSerialize(unittest.TestCase):
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
        
    import logging
    aidalogger.setLevel(logging.DEBUG)
    
    unittest.main()
