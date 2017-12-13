from aiida.orm.node import Node
from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import LinkType


 
class TestParsers(AiidaTestCase):
    def test_link_nonstored_node(self):
        """
        A link between two unstored nodes should be possible
        """
        n1=Node()
        n2=Node()
        n1.add_link_from(n2,label='test')
    def test_link_stored_output_node(self):
        """
        A link of type CREATE should not be allowed between unstored input 
        node and stored output node
        """
        n1=Node()
        n2=Node()
        n2.store()
        self.assertRaises(Exception, n2.add_link_from, n1, label='test', link_type=LinkType.CREATE)
    def test_link_stored_input_node(self):
        """
        A link between stored input node and unstored output node should always be possible
        """
        n1=Node()
        n2=Node()
        n2.store()
        n2.add_link_from(n1,label='test', link_type=LinkType.CREATE)
