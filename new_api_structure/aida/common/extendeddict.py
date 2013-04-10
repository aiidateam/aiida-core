import cPickle
import copy

from aida.common import aidalogger

## TODO: when a KeyError is raised accessing an Attribute, the corresponding
##       AttributeError should be rised instead; corrects tests and code
## To fix: problem with deepcopies, not really well implemented for nested dicts

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
        item = self[attr]
#        return AttributeDict(item) if type(item) == dict else item
        return item

    def __setattr__(self, attr, value):
        self[attr] = value

    def __delattr__(self, attr):
        del self[attr]

    def __getstate__(self): 
        ''' Needed for cPickle in .copy() '''
        return self.__dict__.copy() 

    def __setstate__(self,dict): 
        ''' Needed for cPickle in .copy() '''
        self.__dict__.update(dict)   

    def copy(self):
        return cPickle.loads(cPickle.dumps(self))

    def __deepcopy__(self, memo={}):
        from copy import deepcopy
        print id(self['x']['a']), type(self.x)
        retval = deepcopy(dict(self))
        return self.__class__(retval)


if __name__ == "__main__":
    import unittest

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
            with self.assertRaises(KeyError):
                a = d.test

        def test_access_nonexisting_askey(self):
            d = AttributeDict()
            with self.assertRaises(KeyError):
                a = d['test']
    
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
            with self.assertRaises(KeyError):
                _ = d1.x
            with self.assertRaises(KeyError):
                _ = d1['y']
            self.assertEquals(d2['x'], 'a')
            self.assertEquals(d2.y, 'b')
            self.assertEquals(set(d1.keys()), set({}))
            self.assertEquals(set(d2.keys()), set({'x', 'y'}))
            
        def test_nestedcopy1(self):
            d1 = AttributeDict()
            d1.x = [1,2,3]
            d2 = d1.copy()
            d2.x[0] = 4
            self.assertEquals(d1.x, [1,2,3])
            self.assertEquals(d2.x, [4,2,3])

        def test_nestedcopy2(self):
            """
            Also test access at nested levels
            """
            d1 = AttributeDict()
            d1.x = {'a': 'b', 'c': 'd'}
            d2 = copy.deepcopy(d1)
            # doesn't work like this, would work as d2['x']['a']
            # i think that it is because deepcopy on dict actually creates a
            # copy only if the data is changed; but for a nested dict,
            # d2.x returns a dict wrapped in our class and this looses all the
            # information on what should be updated when changed.
            d2.x.a = 'ggg'
            self.assertEquals(d1.x.a, 'b')
            self.assertEquals(d2.x.a, 'ggg')

            

    import logging
#    aidalogger.setLevel(logging.DEBUG)
    
    unittest.main()
