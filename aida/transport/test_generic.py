import unittest
import logging

class TestGeneric(unittest.TestCase):
    """
    Test whoami on localhost.
    """
    def test_whoami(self):
        import getpass
        from plugins.local import LocalTransport
        with LocalTransport() as t:
            self.assertEquals( t.whoami() , getpass.getuser() )
 
if __name__ == '__main__':
    unittest.main()
