"""
This file contains tests for AIDA.
They are executed when when you run "manage.py test" or
"manage.py test main" (much faster)

"""
from django.utils import unittest
import aida
from aida.djsite.main.models import CalcStatus, CalcType, Code, CodeStatus
from aida.djsite.main.models import CodeType, Computer, Project, Calc
from aida.djsite.main.models import Element, Potential, PotentialStatus, PotentialType
from django.contrib.auth.models import User as AuthUser
import getpass
from django.db import IntegrityError
from django.core import management
import json
import os, os.path
import aida.djsite.main
from aida.repository.potential import add_pseudo_file
from aida.common.exceptions import ValidationError
from aida.common.classes import structure
from aida.repository.structure import add_structure

# Get the absolute path of the testdata folder, related to the aida module
testdata_folder = os.path.join(
    os.path.dirname(os.path.abspath(aida.__file__)),os.path.pardir,'testdata')


class PseudoTest(unittest.TestCase):
    """
    Test for the pseudopotentials 'Potential' table
    """
    @classmethod
    def setUpClass(cls):
        """
        Set up things once for all tests of this class. 
        In particular, defines a type and a status.
        """
        cls.user, was_created = AuthUser.objects.get_or_create(
            username=getpass.getuser())
        cls.status, was_created = PotentialStatus.objects.get_or_create(
            title='Unknown')
        cls.type, was_created = PotentialType.objects.get_or_create(title='pz')
    

    def step1(self):
        """
        Tests insertion of a new pseudo.
        """
        self.new_pot = add_pseudo_file(os.path.join(testdata_folder,
                                                    'Si.pbe-rrkj.UPF'),
                                       description="Test pseudo for Si",
                                       element_symbols=['Si'], pot_type=self.type,
                                       pot_status=self.status,user=self.user)
        
    def step1b(self):
        """
        Check M2M relationships on the newly-created potential.
        """
        self.assertEqual(self.new_pot.element.count(),1)
        self.assertEqual(self.new_pot.element.get().title,'Si')

    def step2(self):
        """
        Test insertion of a pseudo which is identical to the previous one (same 
        md5sum) to see if the function returns the same id instead of adding a
        copy of the pseudo.
        """
        new_pot2 = add_pseudo_file(os.path.join(testdata_folder,
            'Si.pbe-rrkj_copy.UPF'),
            description="Test pseudo for Si - just a file copy",
            element_symbols=['Si'], pot_type=self.type,
            pot_status=self.status,user=self.user)
        self.assertEqual(self.new_pot.id, new_pot2.id)

    def step3(self):
        """
        Test insertion of a pseudo which has a different md5sum (I just modified 
        slightly the content) but with a name that maps on the same name, 
        to see if the title-name generator does it work.
        Test also the algorithm itself for bad symbols removal.
        
        Note:
            actually, the name is different, but the + character is not allowed
            and is stripped out; then, the comparison is done, and the code should
            find a name clash and append a different number to the filename.
        """
        new_pot2 = add_pseudo_file(os.path.join(testdata_folder,
             'Si.pbe-rrkj++.UPF'),
             description=("Test pseudo for Si - similar filename, "
                          "different MD5sum"),
             element_symbols=['Si'], pot_type=self.type,
             pot_status=self.status,user=self.user)
        self.assertEqual(new_pot2.title, 'Si.pbe-rrkj-1.UPF')

    def step4(self):
        """
        Test insertion of a pseudo referring to an element that does not
        exist.
        """
        with self.assertRaises(ValidationError):
            new_pot2 = add_pseudo_file(os.path.join(testdata_folder,
                 'Si.pbe-rrkj.UPF'),
                 description=("Test pseudo for Si - with wrong "
                              "element list"),
                 element_symbols=['inexistent'], pot_type=self.type,
                 pot_status=self.status,user=self.user)

    def the_steps(self):
        for name in sorted(dir(self)):
            if name.startswith("step"):
                yield name, getattr(self, name) 

    def test_steps(self):
        for name, step in self.the_steps():
            try:
                step()
            except Exception as e:
                self.fail("{} failed ({}: {})".format(step.__name__, e.__class__.__name__, e))
                          
class ElementTest(unittest.TestCase):
    """
    Test if elements have been loaded correctly
    """    
    def test_atoms(self):
        """
        Tests chemical symbols and masses of a few atoms (H, C, O, Ba, Ti).
        """
        a = Element.objects.get(Z=1)
        self.assertEqual(a.title, "H")

        a = Element.objects.get(Z=6)
        self.assertEqual(a.title, "C")

        a = Element.objects.get(Z=8)
        self.assertEqual(a.title, "O")

        # Test also the other way round
        a = Element.objects.get(title="Ba")
        self.assertEqual(a.Z, 56)

        a = Element.objects.get(title="Ti")
        self.assertEqual(a.Z, 22)
                         
    def test_no_zequalszero(self):
        """
        Test that there is no element with Z=0.
        """
        from django.core.exceptions import ObjectDoesNotExist
        with self.assertRaises(ObjectDoesNotExist):
            Element.objects.get(Z=0)
        

class SubmissionTest(unittest.TestCase):
    # List here fixtures to be load
    # for some reasons it doesn't work... for the moment I just load it in
    # setUp, even if possibly redundant
    #fixtures = ['testcalcstatus']

    def test_submission(self):
        """
        Tests that I can submit a calculation.
        """
        testuser, was_created = AuthUser.objects.get_or_create(
            username=getpass.getuser())
        # To be loaded in the correct order!
        management.call_command('loaddata', 'testproject', verbosity=0)
        management.call_command('loaddata', 'testcomputer', verbosity=0)
        management.call_command('loaddata', 'testcalcstatus', verbosity=0)
        management.call_command('loaddata', 'testcalctype', verbosity=0)
        management.call_command('loaddata', 'testcodestatus', verbosity=0)
        management.call_command('loaddata', 'testcodetype', verbosity=0)
        management.call_command('loaddata', 'testcode', verbosity=0)

        # I insert a new calculation
        code = Code.objects.get(title__istartswith="pw.x")
        computer = code.computer
        project = Project.objects.get(title__istartswith="test")
        initial_status = CalcStatus.objects.get(title="Submitting")
        calc_type = CalcType.objects.get(title="DFT SCF")

        input_data = {
            'CONTROL': {
                'calculation': 'relax',
                'restart_mode': 'from_scratch',
                },
            'SYSTEM': {
                'ibrav': 0,
                'fixed_magnetization': [0.,1.,0.5],
                'nosym': True,
                },
            'ELECTRONS': {
                'mixing_beta': 0.3,
                },
            'K_POINTS': {
                'type': 'automatic',
                'points': [4, 4, 4, 0, 0, 0],
                },
            }

        data_dict={}
        data_dict['input_data'] = input_data
       
        the_data = json.dumps(data_dict)
        self.the_calc = Calc.objects.create(title="test calculation",
                                           computer=computer,
                                           code=code,project=project,
                                           status=initial_status,
                                           type=calc_type,
                                           data=the_data)

        # There are still no input structures attached
        with self.assertRaises(ValidationError):
            self.the_calc.submit()
            
        a = 5.43
        struc = structure.Structure(cell=((a/2.,a/2.,0.),
                                          (a/2.,0.,a/2.),
                                          (0.,a/2.,a/2.)),
                                    pbc=(True,True,True))
        struc.appendSite(structure.StructureSite(symbols='Si',position=(0.,0.,0.)))
        struc.appendSite(structure.StructureSite(symbols='Si',
                                                 position=(a/2.,a/2.,a/2.)))

        
        struc_django = add_structure(struc,title='Si bulk cell',
                                     user=testuser,dim=3)
        self.the_calc.inpstruc.add(struc_django)

        self.the_calc.submit()

