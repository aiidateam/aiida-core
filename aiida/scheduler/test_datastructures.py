import unittest

class TestNodeNumberJobResource(unittest.TestCase):
    def test_init(self):
        """
        Test the __init__ of the NodeNumberJobResource class
        """
        from aiida.scheduler.datastructures import NodeNumberJobResource

        # No empty initialization
        with self.assertRaises(TypeError):
            _ = NodeNumberJobResource()

        # Missing required field
        with self.assertRaises(TypeError):
            _ = NodeNumberJobResource(num_machines=1)
        with self.assertRaises(TypeError):
            _ = NodeNumberJobResource(num_cpus_per_machine=1)
        with self.assertRaises(TypeError):
            _ = NodeNumberJobResource(tot_num_cpus=1)
        
        # Standard info
        jr = NodeNumberJobResource(num_machines=2, num_cpus_per_machine=8)
        self.assertEquals(jr.num_machines,2)
        self.assertEquals(jr.num_cpus_per_machine,8)
        self.assertEquals(jr.get_tot_num_cpus(),16)
        # redundant but consistent information
        jr = NodeNumberJobResource(num_machines=2, num_cpus_per_machine=8,tot_num_cpus=16)
        self.assertEquals(jr.num_machines,2)
        self.assertEquals(jr.num_cpus_per_machine,8)
        self.assertEquals(jr.get_tot_num_cpus(),16)
        # other equivalent ways of specifying the information
        jr = NodeNumberJobResource(num_cpus_per_machine=8,tot_num_cpus=16)
        self.assertEquals(jr.num_machines,2)
        self.assertEquals(jr.num_cpus_per_machine,8)
        self.assertEquals(jr.get_tot_num_cpus(),16)
        # other equivalent ways of specifying the information
        jr = NodeNumberJobResource(num_machines=2, tot_num_cpus=16)
        self.assertEquals(jr.num_machines,2)
        self.assertEquals(jr.num_cpus_per_machine,8)
        self.assertEquals(jr.get_tot_num_cpus(),16)
        
        # wrong field name
        with self.assertRaises(TypeError):
            _ = NodeNumberJobResource(num_machines=2, num_cpus_per_machine=8,wrong_name=16)
            
        # Examples of wrong informaton (e.g., number of machines or of nodes < 0
        with self.assertRaises(ValueError):
            _ = NodeNumberJobResource(num_machines=0, num_cpus_per_machine=8)
        with self.assertRaises(ValueError):
            _ = NodeNumberJobResource(num_machines=1, num_cpus_per_machine=0)
        with self.assertRaises(ValueError):
            _ = NodeNumberJobResource(num_machines=1, tot_num_cpus=0)
        with self.assertRaises(ValueError):
            _ = NodeNumberJobResource(num_cpus_per_machine=1, tot_num_cpus=0)
        
        # Examples of inconsistent information
        with self.assertRaises(ValueError):
            _ = NodeNumberJobResource(num_cpus_per_machine=8, num_machines=2, tot_num_cpus=32)

        with self.assertRaises(ValueError):
            _ = NodeNumberJobResource(num_cpus_per_machine=8, tot_num_cpus=15)
        
        