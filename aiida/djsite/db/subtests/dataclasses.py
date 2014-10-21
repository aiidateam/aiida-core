# -*- coding: utf-8 -*-
"""
Tests for specific subclasses of Data
"""
from django.utils import unittest

from aiida.orm import Node
from aiida.common.exceptions import ModificationNotAllowed, UniquenessError
from aiida.djsite.db.testbase import AiidaTestCase
        
__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

class TestCalcStatus(AiidaTestCase):        
    """
    Test the functionality of calculation states.
    """
    def test_state(self):
        from aiida.orm import Calculation
        from aiida.common.datastructures import calc_states
        
        # Use the AiidaTestCase test computer
        
        c = Calculation(computer=self.computer,
                        resources={
                            'num_machines': 1,
                            'num_mpiprocs_per_machine': 1}
                        )        
        # Should be in the NEW state before storing
        self.assertEquals(c.get_state(), calc_states.NEW)
        
        with self.assertRaises(ModificationNotAllowed):
            c._set_state(calc_states.TOSUBMIT)
                    
        c.store()
        # Should be in the NEW state right after storing
        self.assertEquals(c.get_state(), calc_states.NEW)
        
        # Set a different state and check
        c._set_state(calc_states.TOSUBMIT)
        self.assertEquals(c.get_state(), calc_states.TOSUBMIT)
        
        # Set a different state and check
        c._set_state(calc_states.SUBMITTING)
        self.assertEquals(c.get_state(), calc_states.SUBMITTING)
        
        # Try to reset a state and check that the proper exception is raised
        with self.assertRaises(UniquenessError):
            c._set_state(calc_states.SUBMITTING)
        
        # Set a different state and check
        c._set_state(calc_states.FINISHED)
        self.assertEquals(c.get_state(), calc_states.FINISHED)
        
        # Try to set a previous state (that is, going backward from 
        # FINISHED to WITHSCHEDULER, for instance)
        # and check that this is not allowed
        with self.assertRaises(ModificationNotAllowed):
            c._set_state(calc_states.WITHSCHEDULER)
        


class TestSinglefileData(AiidaTestCase):
    """
    Test the SinglefileData class.
    """    
    def test_reload_singlefiledata(self):
        import os
        import tempfile

        from aiida.orm.data.singlefile import SinglefileData


        file_content = 'some text ABCDE'
        with tempfile.NamedTemporaryFile() as f:
            filename = f.name
            basename = os.path.split(filename)[1]
            f.write(file_content)
            f.flush()
            a = SinglefileData(file=filename)

        the_uuid = a.uuid

        self.assertEquals(a.get_folder_list(),[basename])

        with open(a.get_abs_path(basename)) as f:
            self.assertEquals(f.read(), file_content)

        a.store()

        with open(a.get_abs_path(basename)) as f:
            self.assertEquals(f.read(), file_content)
        self.assertEquals(a.get_folder_list(),[basename])

        b = Node.get_subclass_from_uuid(the_uuid)

        # I check the retrieved object
        self.assertTrue(isinstance(b,SinglefileData))
        self.assertEquals(b.get_folder_list(),[basename])
        with open(b.get_abs_path(basename)) as f:
            self.assertEquals(f.read(), file_content)

class TestKindValidSymbols(AiidaTestCase):
    """
    Tests the symbol validation of the
    aiida.orm.data.structure.Kind class.
    """
    def test_bad_symbol(self):
        """
        Should not accept a non-existing symbol.
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols='Hxx')
    
    def test_empty_list_symbols(self):
        """
        Should not accept an empty list
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols=[])
    
    def test_valid_list(self):
        """
        Should not raise any error.
        """
        from aiida.orm.data.structure import Kind

        _ = Kind(symbols=['H','He'],weights=[0.5,0.5])

class TestSiteValidWeights(AiidaTestCase):
    """
    Tests valid weight lists.
    """        
    def test_isnot_list(self):
        """
        Should not accept a non-list, non-number weight
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols='Ba',weights='aaa')
    
    def test_empty_list_weights(self):
        """
        Should not accept an empty list
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols='Ba',weights=[])

    def test_symbol_weight_mismatch(self):
        """
        Should not accept a size mismatch of the symbols and weights
        list.
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols=['Ba','C'],weights=[1.])

        with self.assertRaises(ValueError):
            _ = Kind(symbols=['Ba'],weights=[0.1,0.2])

    def test_negative_value(self):
        """
        Should not accept a negative weight
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols=['Ba','C'],weights=[-0.1,0.3])

    def test_sum_greater_one(self):
        """
        Should not accept a sum of weights larger than one
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols=['Ba','C'],
                     weights=[0.5,0.6])

    def test_sum_one_weights(self):
        """
        Should accept a sum equal to one
        """
        from aiida.orm.data.structure import Kind

        _ = Kind(symbols=['Ba','C'],
                 weights=[1./3.,2./3.])

    def test_sum_less_one_weights(self):
        """
        Should accept a sum equal less than one
        """
        from aiida.orm.data.structure import Kind

        _ = Kind(symbols=['Ba','C'],
                 weights=[1./3.,1./3.])
    
    def test_none(self):
        """
        Should accept None.
        """
        from aiida.orm.data.structure import Kind

        _ = Kind(symbols='Ba',weights=None)


class TestKindTestGeneral(AiidaTestCase):
    """
    Tests the creation of Kind objects and their methods.
    """
    def test_sum_one_general(self):
        """
        Should accept a sum equal to one
        """
        from aiida.orm.data.structure import Kind

        a = Kind(symbols=['Ba','C'],
                 weights=[1./3.,2./3.])
        self.assertTrue(a.is_alloy())
        self.assertFalse(a.has_vacancies())

    def test_sum_less_one_general(self):
        """
        Should accept a sum equal less than one
        """
        from aiida.orm.data.structure import Kind

        a = Kind(symbols=['Ba','C'],
                 weights=[1./3.,1./3.])
        self.assertTrue(a.is_alloy())
        self.assertTrue(a.has_vacancies())

    def test_no_position(self):
        """
        Should not accept a 'positions' parameter
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(position=[0.,0.,0.],symbols=['Ba'],
                     weights=[1.])
    
    def test_simple(self):
        """
        Should recognize a simple element.
        """
        from aiida.orm.data.structure import Kind

        a = Kind(symbols='Ba')
        self.assertFalse(a.is_alloy())
        self.assertFalse(a.has_vacancies())

        b = Kind(symbols='Ba',weights=1.)
        self.assertFalse(b.is_alloy())
        self.assertFalse(b.has_vacancies())

        c = Kind(symbols='Ba',weights=None)
        self.assertFalse(c.is_alloy())
        self.assertFalse(c.has_vacancies())


    def test_automatic_name(self):
        """
        Check the automatic name generator.
        """
        from aiida.orm.data.structure import Kind

        a = Kind(symbols='Ba')
        self.assertEqual(a.name,'Ba')

        a = Kind(symbols=('Si','Ge'),weights=(1./3.,2./3.))
        self.assertEqual(a.name,'GeSi')

        a = Kind(symbols=('Si','Ge'),weights=(0.4,0.5))
        self.assertEqual(a.name,'GeSiX')
        
        # Manually setting the name of the species
        a.name = 'newstring'
        self.assertEqual(a.name,'newstring')

class TestKindTestMasses(AiidaTestCase):
    """
    Tests the management of masses during the creation of Kind objects.
    """
    def test_auto_mass_one(self):
        """
        mass for elements with sum one
        """
        from aiida.orm.data.structure import Kind, _atomic_masses

        a = Kind(symbols=['Ba','C'],
                          weights=[1./3.,2./3.])
        self.assertAlmostEqual(a.mass, 
                               (_atomic_masses['Ba'] + 
                                2.* _atomic_masses['C'])/3.)

    def test_sum_less_one_masses(self):
        """
        mass for elements with sum less than one
        """
        from aiida.orm.data.structure import Kind, _atomic_masses

        a = Kind(symbols=['Ba','C'],
                 weights=[1./3.,1./3.])
        self.assertAlmostEqual(a.mass, 
                               (_atomic_masses['Ba'] + 
                                _atomic_masses['C'])/2.)

    def test_sum_less_one_singleelem(self):
        """
        mass for a single element
        """
        from aiida.orm.data.structure import Kind, _atomic_masses

        a = Kind(symbols=['Ba'])
        self.assertAlmostEqual(a.mass, 
                               _atomic_masses['Ba'])
        
    def test_manual_mass(self):
        """
        mass set manually
        """
        from aiida.orm.data.structure import Kind

        a = Kind(symbols=['Ba','C'],
                 weights=[1./3.,1./3.],
                 mass = 1000.)
        self.assertAlmostEqual(a.mass, 1000.)

class TestStructureDataInit(AiidaTestCase):
    """
    Tests the creation of StructureData objects (cell and pbc).
    """
    def test_cell_wrong_size_1(self):
        """
        Wrong cell size (not 3x3)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            _ = StructureData(cell=((1.,2.,3.),))

    def test_cell_wrong_size_2(self):
        """
        Wrong cell size (not 3x3)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            _ = StructureData(cell=((1.,0.,0.),(0.,0.,3.),(0.,3.)))

    def test_cell_zero_vector(self):
        """
        Wrong cell (one vector has zero length)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            _ = StructureData(cell=((0.,0.,0.),(0.,1.,0.),(0.,0.,1.)))

    def test_cell_zero_volume(self):
        """
        Wrong cell (volume is zero)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            _ = StructureData(cell=((1.,0.,0.),(0.,1.,0.),(1.,1.,0.)))

    def test_cell_ok_init(self):
        """
        Correct cell
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
        a = StructureData(cell=cell)
        out_cell = a.cell
        
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(cell[i][j],out_cell[i][j])
    
    def test_volume(self):
        """
        Check the volume calculation
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.)))
        self.assertAlmostEqual(a.get_cell_volume(), 6.)

    def test_wrong_pbc_1(self):
        """
        Wrong pbc parameter (not bool or iterable)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
            _ = StructureData(cell=cell,pbc=1)

    def test_wrong_pbc_2(self):
        """
        Wrong pbc parameter (iterable but with wrong len)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
            _ = StructureData(cell=cell,pbc=[True,True])

    def test_wrong_pbc_3(self):
        """
        Wrong pbc parameter (iterable but with wrong len)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
            _ = StructureData(cell=cell,pbc=[])

    def test_ok_pbc_1(self):
        """
        Single pbc value
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
        a = StructureData(cell=cell,pbc=True)
        self.assertEquals(a.pbc,tuple([True,True,True]))

        a = StructureData(cell=cell,pbc=False)
        self.assertEquals(a.pbc,tuple([False,False,False]))

    def test_ok_pbc_2(self):
        """
        One-element list
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
        a = StructureData(cell=cell,pbc=[True])
        self.assertEqual(a.pbc,tuple([True,True,True]))

        a = StructureData(cell=cell,pbc=[False])
        self.assertEqual(a.pbc,tuple([False,False,False]))

    def test_ok_pbc_3(self):
        """
        Three-element list
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
        a = StructureData(cell=cell,pbc=[True,False,True])
        self.assertEqual(a.pbc,tuple([True,False,True]))

class TestStructureData(AiidaTestCase):
    """
    Tests the creation of StructureData objects (cell and pbc).
    """

    def test_cell_ok_and_atoms(self):
        """
        Test the creation of a cell and the appending of atoms
        """
        from aiida.orm.data.structure import StructureData

        cell = ((2.,0.,0.),(0.,2.,0.),(0.,0.,2.))
        
        a = StructureData(cell=cell)
        out_cell = a.cell
        self.assertAlmostEquals(cell, out_cell)
        
        a.append_atom(position=(0.,0.,0.),symbols=['Ba'])
        a.append_atom(position=(1.,1.,1.),symbols=['Ti'])
        a.append_atom(position=(1.2,1.4,1.6),symbols=['Ti'])
        self.assertFalse(a.is_alloy())
        self.assertFalse(a.has_vacancies())
        # There should be only two kinds! (two atoms of kind Ti should
        # belong to the same kind)
        self.assertEquals(len(a.kinds), 2) 

        a.append_atom(position=(0.5,1.,1.5), symbols=['O', 'C'], 
                         weights=[0.5,0.5])
        self.assertTrue(a.is_alloy())
        self.assertFalse(a.has_vacancies())

        a.append_atom(position=(0.5,1.,1.5), symbols=['O'], weights=[0.5])
        self.assertTrue(a.is_alloy())
        self.assertTrue(a.has_vacancies())

        a.clear_kinds()
        a.append_atom(position=(0.5,1.,1.5), symbols=['O'], weights=[0.5])
        self.assertFalse(a.is_alloy())
        self.assertTrue(a.has_vacancies())

    def test_kind_1(self):
        """
        Test the management of kinds (automatic detection of kind of 
        simple atoms).
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2.,0.,0.),(0.,2.,0.),(0.,0.,2.)))
        
        a.append_atom(position=(0.,0.,0.),symbols=['Ba'])
        a.append_atom(position=(0.5,0.5,0.5),symbols=['Ba'])
        a.append_atom(position=(1.,1.,1.),symbols=['Ti'])
        
        self.assertEqual(len(a.kinds),2) # I should only have two types
        # I check for the default names of kinds
        self.assertEqual(set(k.name for k in a.kinds),
                         set(('Ba', 'Ti')))

    def test_kind_2(self):
        """
        Test the management of kinds (manual specification of kind name).
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2.,0.,0.),(0.,2.,0.),(0.,0.,2.)))
        
        a.append_atom(position=(0.,0.,0.),symbols=['Ba'],name='Ba1')
        a.append_atom(position=(0.5,0.5,0.5),symbols=['Ba'],name='Ba2')
        a.append_atom(position=(1.,1.,1.),symbols=['Ti'])
        
        kind_list = a.kinds
        self.assertEqual(len(kind_list),3) # I should have now three kinds
        self.assertEqual(set(k.name for k in kind_list),
                         set(('Ba1', 'Ba2', 'Ti')))

    def test_kind_3(self):
        """
        Test the management of kinds (adding an atom with different mass).
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2.,0.,0.),(0.,2.,0.),(0.,0.,2.)))
        
        a.append_atom(position=(0.,0.,0.),symbols=['Ba'],mass=100.)
        with self.assertRaises(ValueError):
            # Shouldn't allow, I am adding two sites with the same name 'Ba'
            a.append_atom(position=(0.5,0.5,0.5),symbols=['Ba'],
                          mass=101., name='Ba') 

        # now it should work because I am using a different kind name
        a.append_atom(position=(0.5,0.5,0.5),
                      symbols=['Ba'],mass=101.,name='Ba2') 
            
        a.append_atom(position=(1.,1.,1.),symbols=['Ti'])
        
        self.assertEqual(len(a.kinds),3) # I should have now three types
        self.assertEqual(len(a.sites),3) # and 3 sites
        self.assertEqual(set(k.name for k in a.kinds), set(('Ba', 'Ba2', 'Ti')))

    def test_kind_4(self):
        """
        Test the management of kind (adding an atom with different symbols
        or weights).
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2.,0.,0.),(0.,2.,0.),(0.,0.,2.)))
        
        a.append_atom(position=(0.,0.,0.),symbols=['Ba','Ti'],
                      weights=(1.,0.),name='mytype')

        with self.assertRaises(ValueError):
            # Shouldn't allow, different weights
            a.append_atom(position=(0.5,0.5,0.5),symbols=['Ba','Ti'],
                          weights=(0.9,0.1),name='mytype') 

        with self.assertRaises(ValueError):
            # Shouldn't allow, different weights (with vacancy)
            a.append_atom(position=(0.5,0.5,0.5),symbols=['Ba','Ti'],
                          weights=(0.8,0.1),name='mytype') 

        with self.assertRaises(ValueError):
            # Shouldn't allow, different symbols list
            a.append_atom(position=(0.5,0.5,0.5),symbols=['Ba'],
                          name='mytype') 

        with self.assertRaises(ValueError):
            # Shouldn't allow, different symbols list
            a.append_atom(position=(0.5,0.5,0.5),symbols=['Si','Ti'],
                          weights=(1.,0.),name='mytype') 

        # should allow because every property is identical
        a.append_atom(position=(0.,0.,0.),symbols=['Ba','Ti'],
                      weights=(1.,0.),name='mytype')
        
        self.assertEquals(len(a.kinds), 1)

    def test_kind_5(self):
        """
        Test the management of kinds (automatic creation of new kind
        if name is not specified and properties are different).
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2.,0.,0.),(0.,2.,0.),(0.,0.,2.)))
        
        a.append_atom(position=(0.,0.,0.),symbols='Ba',mass=100.)
        a.append_atom(position=(0.,0.,0.),symbols='Ti')
        # The name does not exist
        a.append_atom(position=(0.,0.,0.),symbols='Ti',name='Ti2')
        # The name already exists, but the properties are identical => OK
        a.append_atom(position=(1.,1.,1.),symbols='Ti',name='Ti2')
        # The name already exists, but the properties are different!
        with self.assertRaises(ValueError):
            a.append_atom(position=(1.,1.,1.),symbols='Ti',mass=100.,name='Ti2')
        # Should not complain, should create a new type
        a.append_atom(position=(0.,0.,0.),symbols='Ba',mass=150.)

        # There should be 4 kinds, the automatic name for the last one
        # should be Ba1
        self.assertEquals([k.name for k in a.kinds],
                          ['Ba', 'Ti', 'Ti2', 'Ba1'])
        self.assertEquals(len(a.sites),5)

    def test_kind_5_bis(self):
        """
        Test the management of kinds (automatic creation of new kind
        if name is not specified and properties are different).
        This test was failing in, e.g., commit f6a8f4b.
        """
        from aiida.orm.data.structure import StructureData
        from aiida.common.constants import elements
        
        s = StructureData(cell=((6.,0.,0.),(0.,6.,0.),(0.,0.,6.)))

        s.append_atom(symbols='Fe', position=[0,0,0], mass=12)
        s.append_atom(symbols='Fe', position=[1,0,0], mass=12)
        s.append_atom(symbols='Fe', position=[2,0,0], mass=12)
        s.append_atom(symbols='Fe', position=[2,0,0])
        s.append_atom(symbols='Fe', position=[4,0,0])

        # I expect only two species, the first one with name 'Fe', mass 12, 
        # and referencing the first three atoms; the second with name
        # 'Fe1', mass = elements[26]['mass'], and referencing the last two atoms
        self.assertEquals(
            set([(k.name, k.mass) for k in s.kinds]),
            set([('Fe', 12.0), ('Fe1', elements[26]['mass'])]))

        kind_of_each_site = [site.kind.name for site in s.sites]
        self.assertEquals(kind_of_each_site,
                          ['Fe', 'Fe', 'Fe', 'Fe1', 'Fe2'])

    def test_kind_6(self):
        """
        Test the returning of kinds from the string name (most of the code
        copied from :py:meth:`.test_kind_5`).
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2.,0.,0.),(0.,2.,0.),(0.,0.,2.)))
        
        a.append_atom(position=(0.,0.,0.),symbols='Ba',mass=100.)
        a.append_atom(position=(0.,0.,0.),symbols='Ti')
        # The name does not exist
        a.append_atom(position=(0.,0.,0.),symbols='Ti',name='Ti2')
        # The name already exists, but the properties are identical => OK
        a.append_atom(position=(1.,1.,1.),symbols='Ti',name='Ti2')
        # Should not complain, should create a new type
        a.append_atom(position=(0.,0.,0.),symbols='Ba',mass=150.)
        # There should be 4 kinds, the automatic name for the last one
        # should be Ba1 (same check of test_kind_5
        self.assertEquals([k.name for k in a.kinds],
                          ['Ba', 'Ti', 'Ti2', 'Ba1'])
        #############################
        # Here I start the real tests        
        # No such kind
        with self.assertRaises(ValueError):
            a.get_kind('Ti3')        
        k = a.get_kind('Ba1')
        self.assertEqual(k.symbols, ('Ba',))
        self.assertAlmostEqual(k.mass, 150.)

    def test_kind_7(self):
        """
        Test the functions returning the list of kinds, symbols, ...
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2.,0.,0.),(0.,2.,0.),(0.,0.,2.)))
        
        a.append_atom(position=(0.,0.,0.),symbols='Ba',mass=100.)
        a.append_atom(position=(0.,0.,0.),symbols='Ti')
        # The name does not exist
        a.append_atom(position=(0.,0.,0.),symbols='Ti',name='Ti2')
        # The name already exists, but the properties are identical => OK
        a.append_atom(position=(0.,0.,0.),symbols=['O', 'H'], weights=[0.9,0.1], mass=15.)

        self.assertEquals(a.get_symbols_set(), set(['Ba', 'Ti', 'O', 'H']))
        

class TestStructureDataLock(AiidaTestCase):
    """
    Tests that the structure is locked after storage
    """
    def test_lock(self):
        """
        Start from a StructureData object, convert to raw and then back
        """
        from aiida.orm.data.structure import StructureData, Kind, Site

        cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
        a = StructureData(cell=cell)
        
        a.pbc = [False,True,True]

        k = Kind(symbols='Ba',name='Ba')       
        s = Site(position=(0.,0.,0.),kind_name='Ba')
        a.append_kind(k)
        a.append_site(s)

        a.append_atom(symbols='Ti', position=[0.,0.,0.])

        a.store()

        k2 = Kind(symbols='Ba',name='Ba')
        # Nothing should be changed after store()
        with self.assertRaises(ModificationNotAllowed):
            a.append_kind(k2)
        with self.assertRaises(ModificationNotAllowed):
            a.append_site(s)
        with self.assertRaises(ModificationNotAllowed):
            a.clear_sites()
        with self.assertRaises(ModificationNotAllowed):
            a.clear_kinds()
        with self.assertRaises(ModificationNotAllowed):
            a.cell = cell
        with self.assertRaises(ModificationNotAllowed):
            a.pbc = [True,True,True]

        _ = a.get_cell_volume()
        _ = a.is_alloy()
        _ = a.has_vacancies()

        b = a.copy()
        # I check that I can edit after copy
        b.append_site(s)
        b.clear_sites()
        # I check that the original did not change
        self.assertNotEquals(len(a.sites), 0)
        b.cell = cell
        b.pbc = [True,True,True]

class TestStructureDataReload(AiidaTestCase):
    """
    Tests the creation of StructureData, converting it to a raw format and
    converting it back.
    """
    def test_reload(self):
        """
        Start from a StructureData object, convert to raw and then back
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
        a = StructureData(cell=cell)
        
        a.pbc = [False,True,True]

        a.append_atom(position=(0.,0.,0.),symbols=['Ba'])
        a.append_atom(position=(1.,1.,1.),symbols=['Ti'])

        a.store()

        b = StructureData(dbnode=a.dbnode)
        
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(cell[i][j], b.cell[i][j])
        
        self.assertEqual(b.pbc, (False,True,True))
        self.assertEqual(len(b.sites), 2)
        self.assertEqual(b.kinds[0].symbols[0], 'Ba')
        self.assertEqual(b.kinds[1].symbols[0], 'Ti')
        for i in range(3):
            self.assertAlmostEqual(b.sites[0].position[i], 0.)
        for i in range(3):
            self.assertAlmostEqual(b.sites[1].position[i], 1.)

        # Fully reload from UUID
        b = StructureData.get_subclass_from_uuid(a.uuid)
        
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(cell[i][j], b.cell[i][j])
        
        self.assertEqual(b.pbc, (False,True,True))
        self.assertEqual(len(b.sites), 2)
        self.assertEqual(b.kinds[0].symbols[0], 'Ba')
        self.assertEqual(b.kinds[1].symbols[0], 'Ti')
        for i in range(3):
            self.assertAlmostEqual(b.sites[0].position[i], 0.)
        for i in range(3):
            self.assertAlmostEqual(b.sites[1].position[i], 1.)


    def test_copy(self):
        """
        Start from a StructureData object, copy it and see if it is preserved
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
        a = StructureData(cell=cell)
        
        a.pbc = [False,True,True]

        a.append_atom(position=(0.,0.,0.),symbols=['Ba'])
        a.append_atom(position=(1.,1.,1.),symbols=['Ti'])

        b = a.copy()        
        
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(cell[i][j], b.cell[i][j])
        
        self.assertEqual(b.pbc, (False,True,True))
        self.assertEqual(len(b.kinds), 2)
        self.assertEqual(len(b.sites), 2)
        self.assertEqual(b.kinds[0].symbols[0], 'Ba')
        self.assertEqual(b.kinds[1].symbols[0], 'Ti')
        for i in range(3):
            self.assertAlmostEqual(b.sites[0].position[i], 0.)
        for i in range(3):
            self.assertAlmostEqual(b.sites[1].position[i], 1.)

        a.store()

        # Copy after store()
        c = a.copy()
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(cell[i][j], c.cell[i][j])
        
        self.assertEqual(c.pbc, (False,True,True))
        self.assertEqual(len(c.kinds), 2)
        self.assertEqual(len(c.sites), 2)
        self.assertEqual(c.kinds[0].symbols[0], 'Ba')
        self.assertEqual(c.kinds[1].symbols[0], 'Ti')
        for i in range(3):
            self.assertAlmostEqual(c.sites[0].position[i], 0.)
        for i in range(3):
            self.assertAlmostEqual(c.sites[1].position[i], 1.)

class TestStructureDataFromAse(AiidaTestCase):
    """
    Tests the creation of Sites from/to a ASE object.
    """
    from aiida.orm.data.structure import has_ase

    @unittest.skipIf(not has_ase(),"Unable to import ase")
    def test_ase(self):
        from aiida.orm.data.structure import StructureData
        import ase

        a = ase.Atoms('SiGe',cell=(1.,2.,3.),pbc=(True,False,False))
        a.set_positions(
            ((0.,0.,0.),
             (0.5,0.7,0.9),)
            )
        a[1].mass = 110.2

        b = StructureData(ase=a)
        c = b.get_ase()

        self.assertEqual(a[0].symbol, c[0].symbol)
        self.assertEqual(a[1].symbol, c[1].symbol)
        for i in range(3):
            self.assertAlmostEqual(a[0].position[i], c[0].position[i])
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(a.cell[i][j], c.cell[i][j])
           
        self.assertAlmostEqual(c[1].mass, 110.2)

    @unittest.skipIf(not has_ase(),"Unable to import ase")
    def test_conversion_of_types_1(self):
        from aiida.orm.data.structure import StructureData
        import ase

        a = ase.Atoms('Si4Ge4',cell=(1.,2.,3.),pbc=(True,False,False))
        a.set_positions(
            ((0.0,0.0,0.0),
             (0.1,0.1,0.1),
             (0.2,0.2,0.2),
             (0.3,0.3,0.3),
             (0.4,0.4,0.4),
             (0.5,0.5,0.5),
             (0.6,0.6,0.6),
             (0.7,0.7,0.7),
             )
            )

        a.set_tags((0,1,2,3,4,5,6,7))

        b = StructureData(ase=a)
        self.assertEquals([k.name for k in b.kinds],
                          ["Si", "Si1", "Si2", "Si3",
                           "Ge4", "Ge5", "Ge6", "Ge7"])
        c = b.get_ase()

        a_tags = list(a.get_tags())
        c_tags = list(c.get_tags())
        self.assertEqual(a_tags, c_tags)

    @unittest.skipIf(not has_ase(),"Unable to import ase")
    def test_conversion_of_types_2(self):
        from aiida.orm.data.structure import StructureData
        import ase

        a = ase.Atoms('Si4',cell=(1.,2.,3.),pbc=(True,False,False))
        a.set_positions(
            ((0.0,0.0,0.0),
             (0.1,0.1,0.1),
             (0.2,0.2,0.2),
             (0.3,0.3,0.3),
             )
            )

        a.set_tags((0,1,0,1))
        a[2].mass = 100.
        a[3].mass = 300.
        
        b = StructureData(ase=a)
        # This will give funny names to the kinds, because I am using
        # both tags and different properties (mass). I just check to have
        # 4 kinds
        self.assertEquals(len(b.kinds), 4)

        # Do I get the same tags after one full iteration back and forth?
        c = b.get_ase()
        d = StructureData(ase=c)
        e = d.get_ase()       
        c_tags = list(c.get_tags())
        e_tags = list(e.get_tags())
        self.assertEqual(c_tags, e_tags)      
        
        
    @unittest.skipIf(not has_ase(),"Unable to import ase")
    def test_conversion_of_types_3(self):
        from aiida.orm.data.structure import StructureData

        a = StructureData()
        a.append_atom(position=(0.,0.,0.), symbols='Ba', name='Ba')
        a.append_atom(position=(0.,0.,0.), symbols='Ba', name='Ba1')
        a.append_atom(position=(0.,0.,0.), symbols='Cu', name='Cu')
        # continues with a number
        a.append_atom(position=(0.,0.,0.), symbols='Cu', name='Cu2')
        # does not continue with a number
        a.append_atom(position=(0.,0.,0.), symbols='Cu', name='Cu_my')
        # random string
        a.append_atom(position=(0.,0.,0.), symbols='Cu', name='a_name')
        # a name of another chemical symbol
        a.append_atom(position=(0.,0.,0.), symbols='Cu', name='Fe')
        # lowercase! as if it were a random string
        a.append_atom(position=(0.,0.,0.), symbols='Cu', name='cu1') 
        
        # Just to be sure that the species were saved with the correct name
        # in the first place
        self.assertEquals([k.name for k in a.kinds], 
                          ['Ba', 'Ba1', 'Cu', 'Cu2', 'Cu_my',
                           'a_name', 'Fe', 'cu1'])
        
        b = a.get_ase()
        self.assertEquals(b.get_chemical_symbols(), ['Ba', 'Ba', 'Cu', 
                                                     'Cu', 'Cu', 'Cu', 
                                                     'Cu', 'Cu'])
        self.assertEquals(list(b.get_tags()), [0, 1, 0, 2, 3, 4, 5, 6])


class TestArrayData(AiidaTestCase):
    """
    Tests the ArrayData objects.
    """

    def test_creation(self):
        """
        Check the methods to add, remove, modify, and get arrays and
        array shapes.
        """
        from aiida.orm.data.array import ArrayData
        import numpy
        
        # Create a node with two arrays
        n = ArrayData()
        first = numpy.random.rand(2,3,4)
        n.set_array('first', first)
        
        second = numpy.arange(10)
        n.set_array('second', second)

        third = numpy.random.rand(6,6)
        n.set_array('third', third)

        
        # Check if the arrays are there
        self.assertEquals(set(['first', 'second', 'third']), set(n.arraynames()))
        self.assertAlmostEquals(abs(first-n.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second-n.get_array('second')).max(), 0.)
        self.assertAlmostEquals(abs(third-n.get_array('third')).max(), 0.)
        self.assertEquals(first.shape, n.get_shape('first'))
        self.assertEquals(second.shape, n.get_shape('second')) 
        self.assertEquals(third.shape, n.get_shape('third')) 
        
        with self.assertRaises(KeyError):
            n.get_array('nonexistent_array')
        
        # Delete an array, and try to delete a non-existing one
        n.delete_array('third')
        with self.assertRaises(KeyError):
            n.delete_array('nonexistent_array')
          
        # Overwrite an array
        first = numpy.random.rand(4,5,6)
        n.set_array('first', first)
        
        # Check if the arrays are there, and if I am getting the new one
        self.assertEquals(set(['first', 'second']), set(n.arraynames()))
        self.assertAlmostEquals(abs(first-n.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second-n.get_array('second')).max(), 0.)
        self.assertEquals(first.shape, n.get_shape('first'))
        self.assertEquals(second.shape, n.get_shape('second')) 
        
        n.store()
        
        # Same checks, after storing
        self.assertEquals(set(['first', 'second']), set(n.arraynames()))
        self.assertAlmostEquals(abs(first-n.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second-n.get_array('second')).max(), 0.)
        self.assertEquals(first.shape, n.get_shape('first'))
        self.assertEquals(second.shape, n.get_shape('second')) 

        # Same checks, again (this is checking the caching features)
        self.assertEquals(set(['first', 'second']), set(n.arraynames()))
        self.assertAlmostEquals(abs(first-n.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second-n.get_array('second')).max(), 0.)
        self.assertEquals(first.shape, n.get_shape('first'))
        self.assertEquals(second.shape, n.get_shape('second')) 


        # Same checks, after reloading
        n2 = ArrayData(dbnode=n.dbnode)
        self.assertEquals(set(['first', 'second']), set(n2.arraynames()))
        self.assertAlmostEquals(abs(first-n2.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second-n2.get_array('second')).max(), 0.)
        self.assertEquals(first.shape, n2.get_shape('first'))
        self.assertEquals(second.shape, n2.get_shape('second')) 

        # Same checks, after reloading with UUID
        n2 = ArrayData.get_subclass_from_uuid(n.uuid)
        self.assertEquals(set(['first', 'second']), set(n2.arraynames()))
        self.assertAlmostEquals(abs(first-n2.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second-n2.get_array('second')).max(), 0.)
        self.assertEquals(first.shape, n2.get_shape('first'))
        self.assertEquals(second.shape, n2.get_shape('second')) 


        # Check that I cannot modify the node after storing
        with self.assertRaises(ModificationNotAllowed):
            n.delete_array('first')
        with self.assertRaises(ModificationNotAllowed):
            n.set_array('second', first)
            
        # Again same checks, to verify that the attempts to delete/overwrite
        # arrays did not damage the node content
        self.assertEquals(set(['first', 'second']), set(n.arraynames()))
        self.assertAlmostEquals(abs(first-n.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second-n.get_array('second')).max(), 0.)
        self.assertEquals(first.shape, n.get_shape('first'))
        self.assertEquals(second.shape, n.get_shape('second')) 
        
    def test_iteration(self):
        """
        Check the functionality of the iterarrays() iterator
        """
        from aiida.orm.data.array import ArrayData
        import numpy
        
        # Create a node with two arrays
        n = ArrayData()
        first = numpy.random.rand(2,3,4)
        n.set_array('first', first)
        
        second = numpy.arange(10)
        n.set_array('second', second)

        third = numpy.random.rand(6,6)
        n.set_array('third', third)
    
        for name, array in n.iterarrays():
            if name == 'first':
                self.assertAlmostEquals(abs(first-array).max(), 0.)
            if name == 'second':
                self.assertAlmostEquals(abs(second-array).max(), 0.)
            if name == 'third':
                self.assertAlmostEquals(abs(third-array).max(), 0.)
        
        
class TestTrajectoryData(AiidaTestCase):
    """
    Tests the TrajectoryData objects.
    """

    def test_creation(self):
        """
        Check the methods to set and retrieve a trajectory.
        """
        from aiida.orm.data.array.trajectory import TrajectoryData
        import numpy
        
        # Create a node with two arrays
        n = TrajectoryData()

        # I create sample data
        steps = numpy.array([60,70])
        times = steps * 0.01
        cells = numpy.array([
                [[2.,0.,0.,],
                 [0.,2.,0.,],
                 [0.,0.,2.,]],
                [[3.,0.,0.,],
                 [0.,3.,0.,],
                 [0.,0.,3.,]]])
        symbols = numpy.array(['H', 'O', 'C'])
        positions = numpy.array([
            [[0.,0.,0.],
             [0.5,0.5,0.5],
             [1.5,1.5,1.5]],
            [[0.,0.,0.],
             [0.5,0.5,0.5],
             [1.5,1.5,1.5]]])
        velocities = numpy.array([
            [[0.,0.,0.],
             [0.,0.,0.],
             [0.,0.,0.]],
            [[0.5,0.5,0.5],
             [0.5,0.5,0.5],
             [-0.5,-0.5,-0.5]]])

        # I set the node
        n.set_trajectory(steps, times, cells, symbols, positions, velocities)

        # Generic checks
        self.assertEqual(n.numsites, 3)
        self.assertEqual(n.numsteps, 2)
        self.assertAlmostEqual(abs(steps-n.get_steps()).sum(), 0.)
        self.assertAlmostEqual(abs(times-n.get_times()).sum(), 0.)
        self.assertAlmostEqual(abs(cells-n.get_cells()).sum(), 0.)
        self.assertEqual(symbols.tolist(), n.get_symbols().tolist())
        self.assertAlmostEqual(abs(positions-n.get_positions()).sum(), 0.)
        self.assertAlmostEqual(abs(velocities-n.get_velocities()).sum(), 0.)
        
        # get_step_data function check
        data = n.get_step_data(1)
        self.assertEqual(data[0], steps[1])
        self.assertAlmostEqual(data[1], times[1])
        self.assertAlmostEqual(abs(cells[1]-data[2]).sum(), 0.)
        self.assertEqual(symbols.tolist(), data[3].tolist())
        self.assertAlmostEqual(abs(data[4]-positions[1]).sum(), 0.)
        self.assertAlmostEqual(abs(data[5]-velocities[1]).sum(), 0.)
        
        # Step 70 has index 1
        self.assertEqual(1,n.get_step_index(70))
        with self.assertRaises(ValueError):
            # Step 66 does not exist
            n.get_step_index(66)
        
        ########################################################
        # I set the node, this time without velocities (the same node)
        n.set_trajectory(steps, times, cells, symbols, positions)
        # Generic checks
        self.assertEqual(n.numsites, 3)
        self.assertEqual(n.numsteps, 2)
        self.assertAlmostEqual(abs(steps-n.get_steps()).sum(), 0.)
        self.assertAlmostEqual(abs(times-n.get_times()).sum(), 0.)
        self.assertAlmostEqual(abs(cells-n.get_cells()).sum(), 0.)
        self.assertEqual(symbols.tolist(), n.get_symbols().tolist())
        self.assertAlmostEqual(abs(positions-n.get_positions()).sum(), 0.)
        self.assertIsNone(n.get_velocities())
        
        # Same thing, but for a new node
        n = TrajectoryData()
        n.set_trajectory(steps, times, cells, symbols, positions)
        # Generic checks
        self.assertEqual(n.numsites, 3)
        self.assertEqual(n.numsteps, 2)
        self.assertAlmostEqual(abs(steps-n.get_steps()).sum(), 0.)
        self.assertAlmostEqual(abs(times-n.get_times()).sum(), 0.)
        self.assertAlmostEqual(abs(cells-n.get_cells()).sum(), 0.)
        self.assertEqual(symbols.tolist(), n.get_symbols().tolist())
        self.assertAlmostEqual(abs(positions-n.get_positions()).sum(), 0.)
        self.assertIsNone(n.get_velocities())
        
        n.store()
        
        # Again same checks, but after storing
        # Generic checks
        self.assertEqual(n.numsites, 3)
        self.assertEqual(n.numsteps, 2)
        self.assertAlmostEqual(abs(steps-n.get_steps()).sum(), 0.)
        self.assertAlmostEqual(abs(times-n.get_times()).sum(), 0.)
        self.assertAlmostEqual(abs(cells-n.get_cells()).sum(), 0.)
        self.assertEqual(symbols.tolist(), n.get_symbols().tolist())
        self.assertAlmostEqual(abs(positions-n.get_positions()).sum(), 0.)
        self.assertIsNone(n.get_velocities())
        
        # get_step_data function check
        data = n.get_step_data(1)
        self.assertEqual(data[0], steps[1])
        self.assertAlmostEqual(data[1], times[1])
        self.assertAlmostEqual(abs(cells[1]-data[2]).sum(), 0.)
        self.assertEqual(symbols.tolist(), data[3].tolist())
        self.assertAlmostEqual(abs(data[4]-positions[1]).sum(), 0.)
        self.assertIsNone(data[5])
        
        # Step 70 has index 1
        self.assertEqual(1,n.get_step_index(70))
        with self.assertRaises(ValueError):
            # Step 66 does not exist
            n.get_step_index(66)

        ##############################################################
        # Again, but after reloading from uuid
        n = TrajectoryData.get_subclass_from_uuid(n.uuid)
        # Generic checks
        self.assertEqual(n.numsites, 3)
        self.assertEqual(n.numsteps, 2)
        self.assertAlmostEqual(abs(steps-n.get_steps()).sum(), 0.)
        self.assertAlmostEqual(abs(times-n.get_times()).sum(), 0.)
        self.assertAlmostEqual(abs(cells-n.get_cells()).sum(), 0.)
        self.assertEqual(symbols.tolist(), n.get_symbols().tolist())
        self.assertAlmostEqual(abs(positions-n.get_positions()).sum(), 0.)
        self.assertIsNone(n.get_velocities())
        
        # get_step_data function check
        data = n.get_step_data(1)
        self.assertEqual(data[0], steps[1])
        self.assertAlmostEqual(data[1], times[1])
        self.assertAlmostEqual(abs(cells[1]-data[2]).sum(), 0.)
        self.assertEqual(symbols.tolist(), data[3].tolist())
        self.assertAlmostEqual(abs(data[4]-positions[1]).sum(), 0.)
        self.assertIsNone(data[5])
        
        # Step 70 has index 1
        self.assertEqual(1,n.get_step_index(70))
        with self.assertRaises(ValueError):
            # Step 66 does not exist
            n.get_step_index(66)

    def test_conversion_to_structure(self):
        """
        Check the methods to export a given time step to a StructureData node.
        """
        from aiida.orm.data.array.trajectory import TrajectoryData
        from aiida.orm.data.structure import Kind
        import numpy

        # Create a node with two arrays
        n = TrajectoryData()

        # I create sample data
        steps = numpy.array([60,70])
        times = steps * 0.01
        cells = numpy.array([
                [[2.,0.,0.,],
                 [0.,2.,0.,],
                 [0.,0.,2.,]],
                [[3.,0.,0.,],
                 [0.,3.,0.,],
                 [0.,0.,3.,]]])
        symbols = numpy.array(['H', 'O', 'C'])
        positions = numpy.array([
            [[0.,0.,0.],
             [0.5,0.5,0.5],
             [1.5,1.5,1.5]],
            [[0.,0.,0.],
             [0.5,0.5,0.5],
             [1.5,1.5,1.5]]])
        velocities = numpy.array([
            [[0.,0.,0.],
             [0.,0.,0.],
             [0.,0.,0.]],
            [[0.5,0.5,0.5],
             [0.5,0.5,0.5],
             [-0.5,-0.5,-0.5]]])

        # I set the node
        n.set_trajectory(steps, times, cells, symbols, positions, velocities)

        struc = n.step_to_structure(1)
        self.assertEqual(len(struc.sites), 3) # 3 sites
        self.assertAlmostEqual(abs(numpy.array(struc.cell)-cells[1]).sum(), 0)
        newpos = numpy.array([s.position for s in struc.sites])
        self.assertAlmostEqual(abs(newpos-positions[1]).sum(), 0)
        newkinds = [s.kind_name for s in struc.sites]
        self.assertEqual(newkinds, symbols.tolist())
        
        # Weird assignments (nobody should ever do this, but it is possible in 
        # principle and we want to check
        k1 = Kind(name='C', symbols='Cu')
        k2 = Kind(name='H', symbols='He')
        k3 = Kind(name='O', symbols='Os', mass=100.)
        k4 = Kind(name='Ge', symbols='Ge')
        
        with self.assertRaises(ValueError):
            # Not enough kinds
            struc = n.step_to_structure(1, custom_kinds=[k1,k2])
        
        with self.assertRaises(ValueError):
            # Too many kinds
            struc = n.step_to_structure(1, custom_kinds=[k1,k2, k3, k4])
        
        with self.assertRaises(ValueError):
            # Wrong kinds
            struc = n.step_to_structure(1, custom_kinds=[k1,k2, k4])
        
        with self.assertRaises(ValueError):
            # Two kinds with the same name
            struc = n.step_to_structure(1, custom_kinds=[k1,k2, k3, k3])

        # Correct kinds
        struc = n.step_to_structure(1, custom_kinds=[k1,k2, k3])
        
        # Checks
        self.assertEqual(len(struc.sites), 3) # 3 sites
        self.assertAlmostEqual(abs(numpy.array(struc.cell)-cells[1]).sum(), 0)
        newpos = numpy.array([s.position for s in struc.sites])
        self.assertAlmostEqual(abs(newpos-positions[1]).sum(), 0)
        newkinds = [s.kind_name for s in struc.sites]
        # Kinds are in the same order as given in the custm_kinds list
        self.assertEqual(newkinds, symbols.tolist())
        newatomtypes = [struc.get_kind(s.kind_name).symbols[0] for s in struc.sites]
        # Atoms remain in the same order as given in the positions list
        self.assertEqual(newatomtypes, ['He', 'Os','Cu'])
        # Check the mass of the kind of the second atom ('O' _> symbol Os, mass 100)
        self.assertAlmostEqual(struc.get_kind(struc.sites[1].kind_name).mass,100.)
        
