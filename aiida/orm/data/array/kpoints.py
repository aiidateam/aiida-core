# -*- coding: utf-8 -*-
"""
This module defines the classes related to band structures or dispersions
in a Brillouin zone, and how to operate on them.
"""

from aiida.orm.data.array import ArrayData
import numpy

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

_default_epsilon_length = 1e-5
_default_epsilon_angle = 1e-5

# TODO: I should check that the cell has three dimensions, maybe it's done somewhere already

class KpointsData(ArrayData):

    def __init__(self,*args,**kwargs):
        super(KpointsData, self).__init__(*args, **kwargs)
        try:
            self._load_cell_properties()
        except AttributeError:
            pass
        
    @property
    def cell(self):
        return numpy.array(self.get_attr('cell'))
        
    @cell.setter
    def cell(self,value):
        self.set_cell(value)
        
    def set_cell(self,value):
        from aiida.common.exceptions import ModificationNotAllowed
        from aiida.orm.data.structure import calc_cell_volume
        if not self._to_be_stored:
            raise ModificationNotAllowed(
                "KpointsData cannot be modified, "
                "it has already been stored")
        
        _volume_threshold = 1.e-6
        try:
            the_cell = tuple(tuple(float(c) for c in i) for i in value)
            if len(the_cell) != 3:
                raise ValueError
            if any(len(i) != 3 for i in the_cell):
                raise ValueError
        except (IndexError,ValueError,TypeError):
            raise ValueError("Cell must be a list of the three vectors, each "
                             "defined as a list of three coordinates.") 
        
        if abs(calc_cell_volume(the_cell)) < _volume_threshold:
            raise ValueError("The cell volume is zero. Invalid cell.")
        
        #the_cell = _get_valid_cell(value)
        self.set_attr('cell',the_cell)
        
    @property
    def pbc(self):
        """
        Get the periodic boundary conditions.
        
        :return: a tuple of three booleans, each one tells if there are periodic
            boundary conditions for the i-th real-space direction (i=1,2,3)
        """
        #return copy.deepcopy(self._pbc)
        return (self.get_attr('pbc1'),self.get_attr('pbc2'),self.get_attr('pbc3'))

    @pbc.setter
    def pbc(self,value):
        self.set_pbc(value)

    def set_pbc(self, value):
        from aiida.common.exceptions import ModificationNotAllowed
        from aiida.orm.data.structure import _get_valid_pbc #TODO: this is not good practice!

        if not self._to_be_stored:
            raise ModificationNotAllowed(
                            "The KpointsData object cannot be modified, "
                            "it has already been stored")
        the_pbc = _get_valid_pbc(value)
        self.set_attr('pbc1',the_pbc[0])
        self.set_attr('pbc2',the_pbc[1])
        self.set_attr('pbc3',the_pbc[2])

    @property
    def labels(self):
        label_numbers = self.get_attr('label_numbers',None)
        labels = self.get_attr('labels',None)
        if labels is None or label_numbers is None:
            return None
        return zip(label_numbers,labels)

    @labels.setter
    def labels(self,value): 
        self.set_labels(value)

    def set_labels(self,value):
        """
        set label names. Must pass in input a list like: [[0,'X'],[34,'L'],... ]
        """
        try:
            label_numbers = [int(i[0]) for i in value]
        except ValueError:
            raise ValueError("The input must contain an integer index, to map"
                             " the labels into the kpoint list")
        labels = [str(i[1]) for i in value]
        
        self.set_attr('label_numbers',label_numbers)
        self.set_attr('labels',labels)

    def append_label(self,value):
        """
        Add a label to the existing ones.
        """
        # get the list of existing labels
        existing_labels = self.labels
        
        # validate the input
        if value.__class__ is not list:
            raise ValueError("Input must be a list of two values: index and label")
        
        if len(value)!=2:
            raise ValueError("Input must be a list of length 2")
        
        try:
            index = int(value[0])
        except ValueError:
            raise ValueError("First item must be an integer kpoint index")
         
        label = str(value[1]) 
        existing_labels.append([index,label])
        
        # overwrite the previous values
        self.set_labels(existing_labels)
     
    def delete_label(self,index):
        """
        Delete the label at position 'index'. Works as the python command 
        del list[index]
        """
        index = int(index)
        existing_labels = self.get_labels()
        del existing_labels[index]
        self.set_labels(existing_labels)

    def set_structure(self,StructureData):
        cell = StructureData.cell
        self.set_structure_from_cell(cell,StructureData.pbc)
    
    def set_structure_from_cell(self,cell,pbc=None):
        """
        "param cell: 3x3 matrix of cell vectors. Orientation: each row 
                     represent a lattice vector
        :param pbc: list of 3 booleans, True if in the first lattice vector
                    direction, there is periodicity.
        """
        self.cell = cell
        if pbc is None:
            pbc = [True,True,True]
        self.pbc = pbc 
        self._load_cell_properties()
        
    def _load_cell_properties(self):
        # save a lot of variables that are used later, and just depend on the
        # cell
        the_cell = numpy.array(self.cell)
        reciprocal_cell = 2.*numpy.pi*numpy.linalg.inv(the_cell)
        self.reciprocal_cell = reciprocal_cell
        self.a1 = numpy.array(the_cell[0,:])
        self.a2 = numpy.array(the_cell[1,:])
        self.a3 = numpy.array(the_cell[2,:])
        self.a = numpy.linalg.norm(self.a1)
        self.b = numpy.linalg.norm(self.a2)
        self.c = numpy.linalg.norm(self.a3)
        self.b1 = reciprocal_cell[0,:]
        self.b2 = reciprocal_cell[1,:]
        self.b3 = reciprocal_cell[2,:]
        self.cosalpha = numpy.dot(self.a2,self.a3)/self.b/self.c
        self.cosbeta  = numpy.dot(self.a3,self.a1)/self.c/self.a
        self.cosgamma = numpy.dot(self.a1,self.a2)/self.a/self.b
        # Note: a,b,c,alpha,beta and gamma are referred to the input cell
        # not to the 'conventional' or rotated cell.

    def set_kpoint_mesh(self,mesh,offset=[0.,0.,0.]):
        from aiida.common.exceptions import ModificationNotAllowed
        # validate
        try:
            the_mesh = tuple(int(i) for i in mesh)
            if len(the_mesh) != 3:
                raise ValueError
        except (IndexError,ValueError,TypeError):
            raise ValueError("The kpoint mesh must be a lits of three integers")
        try:
            the_offset = tuple(float(i) for i in offset)
            if len(the_offset) != 3:
                raise ValueError
        except (IndexError,ValueError,TypeError):
            raise ValueError("The offset must be a list of three integers")
        # check that there is no list of kpoints saved already
        # I cannot have both of them at the same time
        if self.get_array('kpoints',None) is not None:
            raise ModificationNotAllowed("KpointsData has already a kpoint-"
                                         "list stored")
        # store
        self.set_attr('mesh',the_mesh)
        self.set_attr('mesh_offset',the_offset)

    def get_kpoint_mesh(self):
        mesh = self.get_attr('mesh',None)
        offset = self.get_attr('mesh',None)
        return mesh, offset

    def _validate_kpoints_weights(self,kpoints,weights):
        kpoints = numpy.array(kpoints)
        if kpoints.dtype != numpy.dtype(numpy.float):
            raise ValueError("kpoints must be an array of type floats. "
                             "Found instead {}".format(kpoints.dtype))
        dimension = 3
        if kpoints.shape[1] != dimension:
            raise ValueError("In a system which has {} dimensions, kpoint need"
                             "more than {} coordinates"
                             .format(dimension,kpoints.shape[1]))                             
        if weights is not None:
            weights = numpy.array(weights)
            if len(weights) != kpoints.shape[0]:
                raise ValueError("Found {} weights but {} kpoints"
                                 .format(len(weights), len(kpoints)))
            if weights.dtype != numpy.dtype(numpy.float):
                raise ValueError("weights must be an array of type floats. "
                                 "Found instead {}".format(weights.dtype))
        
        return kpoints,weights

    def set_kpoints_relative(self,kpoints,weights=None,labels=None):
        """
        In units of the reciprocal lattice vectors.
        A list of kpoints, each kpoint being a list of 3 coordinates
        """
        from aiida.common.exceptions import ModificationNotAllowed
        # check that it is a 'dim'x #kpoints dimensional array
        the_kpoints,the_weights = self._validate_kpoints_weights(kpoints,weights)
        
        # check that we did not saved a mesh already
        if self.get_attr('mesh',None) is not None:
            raise ModificationNotAllowed("KpointsData has already a mesh stored")
        
        # store
        self.set_array('kpoints',the_kpoints)
        if the_weights is not None:
            self.set_array('weights',the_weights)
        if labels is not None:
            self.labels = labels
        
    def get_kpoints_relative(self,also_weights=False):
        """
        get the kpoints in units of the dim reciprocal lattice vectors.
        """
        kpoints = numpy.array(self.get_array('kpoints'),None)
        if kpoints is None:
            raise AttributeError("Before the get, first set a list of kpoints")
            
        if not all(self.pbc):
            for i in range(3):
                if not self.pbc[i]:
                    kpoints[:,i] = 0.
        # note that this operation may lead to duplicates if the kpoints were
        # set thinking that everything is 3D.
        # Atm, it's up to the user to avoid duplication, if he cares.
        # in the future, add the bravais_info for 2d and 1d cases, 
        # and do a set() on the kpoints lists (before storing)
            
        if also_weights:
            the_weights = self.get_array('weights',None)
            if the_weights is None:
                raise AttributeError('No weights were set')
            weights = numpy.array(the_weights)
            return kpoints,weights
        else:
            return kpoints

    def set_kpoints_absolute(self,kpoints,weights=None,labels=None):
        relative_kpoints = self._change_reference(kpoints,to_absolute=False)
        self.set_kpoints_relative(relative_kpoints,weights,labels)

    def get_kpoints_absolute(self,also_weights=False):
        if also_weights:
            relative_kpoints,weights = self.get_kpoints_relative(also_weights)
        else:
            relative_kpoints = self.get_kpoints_relative()
        absolute_kpoints = self._change_reference(relative_kpoints,
                                                  to_absolute=True)
        if also_weights:
            return absolute_kpoints,weights
        else:
            return absolute_kpoints
            
    def _change_reference(self,kpoints,to_absolute=True):
        """
        Change reference system, from absolute to relative coordinates of 
        b1,b2,b3 or viceversa.
        """
        try:
            rec_cell = self.reciprocal_cell
        except AttributeError:
            rec_cell = numpy.eye(3)
            # raise InputError("Cannot change coords without cell")
        rec_cell = numpy.transpose( numpy.array(rec_cell) )
        if to_absolute:
            matrix = rec_cell
        else:
            matrix = numpy.linalg.inv(rec_cell)
        
        return numpy.dot(matrix,kpoints)
    
    def path_from_special_points(self,special_points,spacing=None):
        # TODO: UNTESTED!!!
        # validate the input
        if len(special_points)<2:
            raise ValueError("Cannot build a path with less than two points in"
                             "the input special_points")
        try:
            special_labels = [ i['labels'] for i in special_points ]
            special_coords = [ i['coordinates'] for i in special_points ]
        except (IndexError,KeyError):
            ValueError("special_points must be a dictionary in the same format "
                       "of get_special_points")
                       
        # decide the spacing according to what is found
        # put a default like self.a/50.
        reciprocal_cell = self.get_attr('reciprocal_cell',None)
        if spacing is not None:
            # try to keep a 
            if reciprocal_cell is not None:
                spacing = numpy.array(reciprocal_cell)[0,:] / 50.
            else:
                spacing = numpy.array(special_coords[0]) - numpy.array(special_coords[1])
        # convert points into absolute coords
        # if no cell is found, don't transform
        special_coords_abs = self._change_reference(special_coords,to_absolute=True)
        
        # create the path
        label_index = [(0,special_labels[0])]
        path = []
        j = 0
        for i in range(len(special_coords_abs)-1):
            j+=1
            path.append(zip(
                        numpy.arange(special_coords_abs[i][0],special_coords_abs[i+1][0],spacing[0]),
                        numpy.arange(special_coords_abs[i][1],special_coords_abs[i+1][1],spacing[1]),
                        numpy.arange(special_coords_abs[i][2],special_coords_abs[i+1][2],spacing[2]),
                            ))
            label_index.append((len(path),special_labels[j]))
        path.append(special_coords_abs[-1])
        
        # transform it back to relative coordinates
        coords_to_return = self._change_reference(path,to_absolute=False)
        
        return coords_to_return,label_index
        
    def set_path_from_special_points(self,special_points,spacing=None):
        points,labels = self.path_from_special_points(special_points,spacing)
        self.set_kpoints_relative(points)
        self.labels = labels
                
    def get_special_points_absolute(self):
        import copy
        special_points = self.get_special_points_relative()
        the_special_points = []
        for i in special_points:
            a = copy.copy(i)
            a['coordinates'] = self._change_reference(i['coordinates'],to_absolute=True)
            the_special_points.append(a)
        return the_special_points
        
    def _get_bravais_info(self,epsilon_length=_default_epsilon_length,epsilon_angle=_default_epsilon_angle):
        """
        Finds the Bravais lattice of the cell passed in input to the Kpoint class

        :return: a dictionary, with keys short_name, expanded_name, number
        """
        # load vectors
        a1 = self.a1
        a2 = self.a2
        a3 = self.a3
        a = self.a
        b = self.b
        c = self.c
        cosa = self.cosalpha
        cosb = self.cosbeta
        cosc = self.cosgamma
        
        # values of cosines at various angles
        _90 = 0.
        _60 = 0.5
        _30 = numpy.sqrt(3.)/2.
        _120 = -0.5

        # NOTE: in what follows, I'm assuming the textbook order of alfa, beta and gamma

        def l_are_equals(a,b):
            # function to compare lengths
            if abs(a - b) <= epsilon_length:
                return True
            else:
                return False

        def a_are_equals(a,b):
            # function to compare angles (actually, cosines)
            if abs(a - b) <= epsilon_angle:
                return True
            else:
                return False

        comparison_length = [l_are_equals(a,b),l_are_equals(b,c),
                             l_are_equals(c,a)]
        comparison_angles = [a_are_equals(cosa,cosb),a_are_equals(cosb,cosc),
                             a_are_equals(cosc,cosa)]

        if comparison_length.count(True) == 3:

            # needed for the body-centered orthorhombic:
            orci_a = numpy.linalg.norm(a2+a3)
            orci_b = numpy.linalg.norm(a1+a3)
            orci_c = numpy.linalg.norm(a1+a2)
            orci_the_a,orci_the_b, orci_the_c = sorted([orci_a,orci_b,orci_c])
            bco1 = - (-orci_the_a**2 + orci_the_b**2 + orci_the_c**2) / ( 4.*a**2 )
            bco2 = - ( orci_the_a**2 - orci_the_b**2 + orci_the_c**2) / ( 4.*a**2 )
            bco3 = - ( orci_the_a**2 + orci_the_b**2 - orci_the_c**2) / ( 4.*a**2 )
            
            #======================#
            # simple cubic lattice #
            #======================#
            if comparison_angles.count(True) == 3 and a_are_equals(cosa,_90):
                bravais_info = {"short_name":"cub",
                                "extended_name":"cubic",
                                "index":1,
                                "permutation":[0,1,2]
                                }
            #=====================#
            # face centered cubic #
            #=====================#
            elif comparison_angles.count(True)==3 and a_are_equals(cosa,_60):
                bravais_info = {"short_name":"fcc",
                                "extended_name":"face centered cubic",
                                "index":2,
                                "permutation":[0,1,2]
                                }
            #=====================#
            # body centered cubic #
            #=====================#
            elif comparison_angles.count(True)==3 and a_are_equals(cosa,-1./3.):
                bravais_info = {"short_name":"bcc",
                                "extended_name":"body centered cubic",
                                "index":1,
                                "permutation":[0,1,2]
                                }
            #==============#
            # rhombohedral #
            #==============#
            elif comparison_angles.count(True)==3:
                # logical order is important, this check must come after the cubic cases
                bravais_info = {"short_name":"rhl",
                                "extended_name":"rhombohedral",
                                "index":11,
                                "permutation":[0,1,2]
                                }
                if cosa > 0.:
                    bravais_info['variation'] = 'rhl1'
                    eta = (1.+4.*cosa) / (2.+4.*cosa)
                    bravais_info['extra'] = {'eta':eta,
                                             'nu':0.75 - eta/2.,
                                             }
                else:
                    bravais_info['variation'] = 'rhl2'
                    eta = 1. / (2.* (1.-cosa)/(1.+cosa) )
                    bravais_info['extra'] = {'eta':eta,
                                             'nu':0.75 - eta/2.,
                                             }

            #==========================#
            # body centered tetragonal #
            #==========================#
            elif comparison_angles.count(True)==1: # two angles are the same
                bravais_info = {"short_name":"bct",
                                "extended_name":"body centered tetragonal",
                                "index":5,
                                }
                if comparison_angles.index(True)==0: #alfa=beta
                    ref_ang = cosa
                    bravais_info["permutation"] = [0,1,2]
                elif comparison_angles.index(True)==1: # beta=gamma
                    ref_ang = cosb
                    bravais_info["permutation"] = [2,0,1]
                else: # comparison_angles.index(True)==2: # gamma = alfa
                    ref_ang = cosc
                    bravais_info["permutation"] = [1,2,0]

                if ref_ang>=0.:
                    raise ValueError("Problems on the definition of "
                                     "body centered tetragonal lattices")
                the_c = numpy.sqrt( -4.*ref_ang*(a**2) )
                the_a = numpy.sqrt( 2.*a**2 - (the_c**2)/2. )

                if the_c<the_a:
                    bravais_info['variation'] = 'bct1'
                    bravais_info['extra'] = {'eta':(1.+(the_c/the_a)**2)/4.}
                else:
                    bravais_info['variation'] = 'bct2'
                    bravais_info['extra'] = {'eta':(1.+(the_a/the_c)**2)/4.,
                                             'csi':((the_a/the_c)**2)/2.,
                                             }

            #============================#
            # body-centered orthorhmobic #
            #============================#
            elif (any([a_are_equals(cosa,bco1),a_are_equals(cosb,bco1),a_are_equals(cosc,bco1)]) and
                  any([a_are_equals(cosa,bco2),a_are_equals(cosb,bco2),a_are_equals(cosc,bco2)]) and
                  any([a_are_equals(cosa,bco3),a_are_equals(cosb,bco3),a_are_equals(cosc,bco3)])
                  ):
                bravais_info = {"short_name":"orci",
                                "extended_name":"body-centered orthorhombic",
                                "index":8,
                                }
                if a_are_equals(cosa,bco1) and a_are_equals(cosc,bco3):
                    bravais_info['permutation'] = [0,1,2]
                if a_are_equals(cosa,bco1) and a_are_equals(cosc,bco2):
                    bravais_info['permutation'] = [0,2,1]
                if a_are_equals(cosa,bco3) and a_are_equals(cosc,bco2):
                    bravais_info['permutation'] = [1,2,0]
                if a_are_equals(cosa,bco2) and a_are_equals(cosc,bco3):
                    bravais_info['permutation'] = [1,0,2]
                if a_are_equals(cosa,bco2) and a_are_equals(cosc,bco1):
                    bravais_info['permutation'] = [2,0,1]
                if a_are_equals(cosa,bco3) and a_are_equals(cosc,bco1):
                    bravais_info['permutation'] = [2,1,0]

                bravais_info['extra'] = {'csi':(1. + (orci_the_a/orci_the_c)**2)/4.,
                                         'eta':(1. + (orci_the_b/orci_the_c)**2)/4.,
                                         'dlt':(orci_the_b**2 - orci_the_a**2)/(4.*orci_the_c**2),
                                         'mu':(orci_the_a**2 + orci_the_b**2)/(4.*orci_the_c**2),
                                        }
                    
            # if it doesn't fall in the above, is trigonal
            else:
                bravais_info = {"short_name":"tri",
                                "extended_name":"trigonal",
                                "index":14,
                                }
                # the check for trigonal variations is at the end of the method
                


        elif comparison_length.count(True) == 1:
            #============#
            # tetragonal #
            #============#
            if comparison_angles.count(True) == 3 and a_are_equals(cosa,_90):
                bravais_info = {"short_name":"tet",
                                "extended_name":"tetragonal",
                                "index":4,
                                }
                if comparison_length[0]==True:
                    bravais_info["permutation"] = [0,1,2]
                if comparison_length[1]==True:
                    bravais_info["permutation"] = [2,0,1]
                if comparison_length[2]==True:
                    bravais_info["permutation"] = [1,2,0]
            #====================================#
            # c-centered orthorombic + hexagonal #
            #====================================#
            # alpha/=beta=gamma=pi/2
            elif (comparison_angles.count(True) == 1 and 
                  any([a_are_equals(cosa,_90),a_are_equals(cosb,_90),a_are_equals(cosc,_90)])
                  ):
                if any([a_are_equals(cosa,_120),a_are_equals(cosb,_120),a_are_equals(cosc,_120)]):
                    bravais_info = {"short_name":"hex",
                                    "extended_name":"hexagonal",
                                    "index":10,
                                    }
                else:
                    bravais_info = {"short_name":"orcc",
                                    "extended_name":"c-centered orthorhombic",
                                    "index":9,
                                    }
                    if comparison_length[0]==True:
                        the_a1 = a1
                        the_a2 = a2
                    elif comparison_length[1]==True:
                        the_a1 = a2
                        the_a2 = a3
                    else: # comparison_length[2]==True:
                        the_a1 = a3
                        the_a2 = a1
                    the_a = numpy.linalg.norm( the_a1 + the_a2 )
                    the_b = numpy.linalg.norm( the_a1 - the_a2 )
                    bravais_info['extra'] = {'csi':(1. + (the_a/the_b)**2)/4.,
                                            }
                    

                if comparison_length[0]==True:
                    bravais_info["permutation"] = [0,1,2]
                if comparison_length[1]==True:
                    bravais_info["permutation"] = [2,0,1]
                if comparison_length[2]==True:
                    bravais_info["permutation"] = [1,2,0]
            #=======================#
            # c-centered monoclinic #
            #=======================#
            elif comparison_angles.count(True) == 1:
                bravais_info = {"short_name":"mclc",
                                "extended_name":"c-centered monoclinic",
                                "index":13,
                                }
                if comparison_length[0]==True:
                    bravais_info["permutation"] = [0,1,2]
                    the_ka = cosa
                    the_a1 = a1
                    the_a2 = a2
                    the_c = c
                if comparison_length[1]==True:
                    bravais_info["permutation"] = [2,0,1]
                    the_ka = cosb
                    the_a1 = a2
                    the_a2 = a3
                    the_c = a
                if comparison_length[2]==True:
                    bravais_info["permutation"] = [1,2,0]
                    the_ka = cosc
                    the_a1 = a3
                    the_a2 = a1
                    the_c = b
                    
                the_b = numpy.linalg.norm(the_a1+the_a2)
                the_a = numpy.linalg.norm(the_a1-the_a2)
                the_cosa = 2. * numpy.linalg.norm(the_a1) / the_b * the_ka

                if a_are_equals(the_ka,_90): # order matters: has to be before the check on mclc1
                    bravais_info['variation'] = 'mclc2'
                    csi = (2.-the_b*the_cosa/the_c) / (4.*(1.-the_cosa**2))
                    psi = 0.75 - the_a**2/(4.*the_b*(1.-the_cosa**2))
                    bravais_info['extra'] = {'csi':csi,
                                             'eta':0.5+2.*csi*the_c*the_cosa/the_b,
                                             'psi':psi,
                                             'phi':psi + (0.75-psi)*the_b*the_cosa/the_c
                                             }                    
                elif the_ka<0.:
                    bravais_info['variation'] = 'mclc1'
                    csi = (2.-the_b*the_cosa/the_c) / (4.*(1.-the_cosa**2))
                    psi = 0.75 - the_a**2/(4.*the_b*(1.-the_cosa**2))
                    bravais_info['extra'] = {'csi':csi,
                                             'eta':0.5+2.*csi*the_c*the_cosa/the_b,
                                             'psi':psi,
                                             'phi':psi + (0.75-psi)*the_b*the_cosa/the_c
                                             }                    
                else: #if the_ka>0.:
                    x = the_b*the_cosa/the_c+the_b**2*(1.-the_cosa**2)/the_a**2
                    if a_are_equals(x,1.):
                        bravais_info['variation'] = 'mclc4' # order matters here too
                        mu = (1.+(the_b/the_a)**2)/4.
                        dlt = the_b*the_c*the_cosa/(2.*the_a**2)
                        csi = mu - 0.25 + (1.-the_b*the_cosa/the_c)/(4.*(1.-the_cosa**2))
                        eta = 0.5 + 2.*csi*the_c*the_cosa/the_b
                        phi = 1.+eta-2.*mu
                        psi = eta-2.*dlt
                        bravais_info['extra'] = {'mu':mu,
                                                 'dlt':dlt,
                                                 'csi':csi,
                                                 'eta':eta,
                                                 'phi':phi,
                                                 'psi':psi,
                                                 }
                    elif x<1.:
                        bravais_info['variation'] = 'mclc3'
                        mu = (1.+(the_b/the_a)**2)/4.
                        dlt = the_b*the_c*the_cosa/(2.*the_a**2)
                        csi = mu - 0.25 + (1.-the_b*the_cosa/the_c)/(4.*(1.-the_cosa**2))
                        eta = 0.5 + 2.*csi*the_c*the_cosa/the_b
                        phi = 1.+eta-2.*mu
                        psi = eta-2.*dlt
                        bravais_info['extra'] = {'mu':mu,
                                                 'dlt':dlt,
                                                 'csi':csi,
                                                 'eta':eta,
                                                 'phi':phi,
                                                 'psi':psi,
                                                 }
                    elif x>1.:
                        bravais_info['variation'] = 'mclc5'
                        csi = ((the_b/the_a)**2 + (1.-the_b*the_cosa/the_c)/(1.-the_cosa**2))/4.
                        eta = 0.5 +2.*csi*the_c*the_cosa/the_b
                        mu  = eta/2.+the_b**2/4./the_a**2 - the_b*the_c*the_cosa/2./the_a**2
                        nu = 2.*mu-csi
                        omg = (4.*nu -1.-the_b**2*(1.-the_cosa**2)/the_a**2)*the_c/(2.*the_b*the_cosa)
                        dlt = csi*the_c*the_cosa/the_b + omg/2. - 0.25
                        rho = 1. - csi*the_a**2 / the_b**2
                        bravais_info['extra'] = {'mu':mu,
                                                 'dlt':dlt,
                                                 'csi':csi,
                                                 'eta':eta,
                                                 'phi':phi,
                                                 'psi':psi,
                                                 'rho':rho
                                                 }
            
            # if it doesn't fall in the above, is trigonal
            else:
                bravais_info = {"short_name":"tri",
                                "extended_name":"trigonal",
                                "index":14,
                                }
                # the check for trigonal variations is at the end of the method



        else: #if comparison_length.count(True)==0:

            fco1 = c**2 / numpy.sqrt((a**2+c**2)*(b**2+c**2))
            fco2 = a**2 / numpy.sqrt((a**2+b**2)*(a**2+c**2))
            fco3 = b**2 / numpy.sqrt((a**2+b**2)*(b**2+c**2))
            #==============#
            # orthorhombic #
            #==============#
            if comparison_angles.count(True)==3:
                bravais_info = {"short_name":"orc",
                                "extended_name":"orthorhombic",
                                "index":6,
                                }
                lens = [a,b,c]
                ind_a = lens.index(min(lens))
                ind_c = lens.index(max(lens))
                if ind_a==0 and ind_c==1:
                    bravais_info["permutation"] = [0,2,1]
                if ind_a==0 and ind_c==2:
                    bravais_info["permutation"] = [0,1,2]
                if ind_a==1 and ind_c==0:
                    bravais_info["permutation"] = [1,0,2]
                if ind_a==1 and ind_c==2:
                    bravais_info["permutation"] = [1,0,2]
                if ind_a==2 and ind_c==0:
                    bravais_info["permutation"] = [2,1,0]
                if ind_a==2 and ind_c==1:
                    bravais_info["permutation"] = [2,0,1]
            #============#
            # monoclinic #
            #============#
            elif (comparison_angles.count(True)==1 and
                  any([a_are_equals(cosa,_90),a_are_equals(cosb,_90),a_are_equals(cosc,_90)]) ):
                bravais_info = {"short_name":"mcl",
                                "extended_name":"monoclinic",
                                "index":12,
                                }
                lens = [a,b,c]
                # find the angle different from 90
                # then order (if possible) a<b<c
                if not a_are_equals(cosa,_90):
                    the_cosa = cosa
                    the_a = min(a,b)
                    the_b = max(a,b)
                    the_c = c
                    if lens.index(the_a)==0:
                        bravais_info['permutation'] = [0,1,2]
                    else:
                        bravais_info['permutation'] = [1,0,2]
                elif not a_are_equals(cosb,_90):
                    the_cosa = cosb
                    the_a = min(a,c)
                    the_b = max(a,c)
                    the_c = b
                    if lens.index(the_a)==0:
                        bravais_info['permutation'] = [0,2,1]
                    else:
                        bravais_info['permutation'] = [1,2,0]
                else: #if not _are_equals(cosc,_90):
                    the_cosa = cosc
                    the_a = min(b,c)
                    the_b = max(b,c)
                    the_c = a
                    if lens.index(the_a)==1:
                        bravais_info['permutation'] = [2,0,1]
                    else:
                        bravais_info['permutation'] = [2,1,0]
                eta = (1.-the_b*the_cosa/the_c) / (2.*(1.-the_cosa**2))
                bravais_info['extra'] = {'eta':eta,
                                         'nu':0.5-eta*the_c*the_cosa/the_b,
                                         }
            #============================#
            # face-centered orthorhombic #
            #============================#
            elif (any([a_are_equals(cosa,fco1),a_are_equals(cosb,fco1),a_are_equals(cosc,fco1)]) and
                  any([a_are_equals(cosa,fco2),a_are_equals(cosb,fco2),a_are_equals(cosc,fco2)]) and
                  any([a_are_equals(cosa,fco3),a_are_equals(cosb,fco3),a_are_equals(cosc,fco3)])
                  ):
                bravais_info = {"short_name":"orcf",
                                "extended_name":"face-centered orthorhombic",
                                "index":7,
                                }

                lens = [a,b,c]
                ind_a1 = lens.index(max(lens))
                ind_a3 = lens.index(min(lens))
                if ind_a1 == 0 and ind_a3 == 2:
                    bravais_info['permutation'] = [0,1,2]
                    the_a1 = a1
                    the_a2 = a2
                    the_a3 = a3
                elif ind_a1 == 0 and ind_a3 == 1:
                    bravais_info['permutation'] = [0,2,1]
                    the_a1 = a1
                    the_a2 = a3
                    the_a3 = a2
                elif ind_a1 == 1 and ind_a3 == 2:
                    bravais_info['permutation'] = [1,0,2]
                    the_a1 = a2
                    the_a2 = a1
                    the_a3 = a3
                elif ind_a1 == 1 and ind_a3 == 0:
                    bravais_info['permutation'] = [2,0,1]
                    the_a1 = a3
                    the_a2 = a1
                    the_a3 = a2
                elif ind_a1 == 2 and ind_a3 == 1:
                    bravais_info['permutation'] = [1,2,0]
                    the_a1 = a2
                    the_a2 = a3
                    the_a3 = a1
                else:#  ind_a1 == 2 and ind_a3 == 0:
                    bravais_info['permutation'] = [2,1,0]
                    the_a1 = a3
                    the_a2 = a2
                    the_a3 = a1
                    
                the_a = numpy.linalg.norm( - the_a1 + the_a2 + the_a3)
                the_b = numpy.linalg.norm( + the_a1 - the_a2 + the_a3)
                the_c = numpy.linalg.norm( + the_a1 + the_a2 - the_a3)
                    
                fco4 = 1./the_a**2 - 1./the_b**2 - 1./the_c**2
                #orcf3
                if a_are_equals(fco4,0.):
                    bravais_info['variation'] = 'orcf3' # order matters
                    bravais_info['extra'] = {'csi':(1.+(the_a/the_b)**2 - (the_a/the_c)**2)/4.,
                                             'eta':(1.+(the_a/the_b)**2 + (the_a/the_c)**2)/4.,
                                             }
                # orcf1 
                elif fco4 > 0.:
                    bravais_info['variation'] = 'orcf1'
                    bravais_info['extra'] = {'csi':(1.+(the_a/the_b)**2 - (the_a/the_c)**2)/4.,
                                             'eta':(1.+(the_a/the_b)**2 + (the_a/the_c)**2)/4.,
                                             }
                #orcf2
                else:
                    bravais_info['variation'] = 'orcf2'
                    bravais_info['extra'] = {'eta':(1.+(the_a/the_b)**2 - (the_a/the_c)**2)/4.,
                                             'dlt':(1.+(the_b/the_a)**2 + (the_b/the_c)**2)/4.,
                                             'phi':(1.+(the_c/the_b)**2 - (the_c/the_a)**2)/4.,
                                             }

            else: 
                bravais_info = {"short_name":"tri",
                                "extended_name":"triclinic",
                                "index":14,
                                }
        #===========#
        # triclinic #
        #===========#
        # still miss the variations of triclinic
        if bravais_info['short_name'] == 'tri':
            lens = [a,b,c]
            ind_a = lens.index(min(lens))
            ind_c = lens.index(max(lens))
            if ind_a==0 and ind_c==1:
                the_a = a
                the_b = c
                the_c = b
                the_cosa = cosa
                the_cosb = cosc
                the_cosc = cosb
                bravais_info["permutation"] = [0,2,1]
            if ind_a==0 and ind_c==2:
                the_a = a
                the_b = b
                the_c = c
                the_cosa = cosa
                the_cosb = cosb
                the_cosc = cosc
                bravais_info["permutation"] = [0,1,2]
            if ind_a==1 and ind_c==0:
                the_a = b
                the_b = c
                the_c = a
                the_cosa = cosb
                the_cosb = cosc
                the_cosc = cosa
                bravais_info["permutation"] = [1,0,2]
            if ind_a==1 and ind_c==2:
                the_a = b
                the_b = a
                the_c = c
                the_cosa = cosb
                the_cosb = cosa
                the_cosc = cosc
                bravais_info["permutation"] = [1,0,2]
            if ind_a==2 and ind_c==0:
                the_a = c
                the_b = b
                the_c = a
                the_cosa = cosc
                the_cosb = cosb
                the_cosc = cosa
                bravais_info["permutation"] = [2,1,0]
            if ind_a==2 and ind_c==1:
                the_a = c
                the_b = a
                the_c = b
                the_cosa = cosc
                the_cosb = cosa
                the_cosc = cosb
                bravais_info["permutation"] = [2,0,1]

            if the_cosa < 0. and the_cosb < 0.:
                if a_are_equals(the_cosc,0.):
                    bravais_info['variation'] = 'tri2a'
                elif the_cosc<0.:
                    bravais_info['variation'] = 'tri1a'
                else:
                    raise ValueError("Structure erroneously fell into the triclinic (a) case")
            elif the_cosa > 0. and the_cosb > 0.:
                if a_are_equals(the_cosc,0.):
                    bravais_info['variation'] = 'tri2b'
                elif the_cosc > 0.:
                    bravais_info['variation'] = 'tri1b'
                else:
                    raise ValueError("Structure erroneously fell into the triclinic (b) case")
            else:
                raise ValueError("Structure erroneously fell into the triclinic case")

        return bravais_info

    def get_bravais_lattice(self,epsilon_length=_default_epsilon_length,epsilon_angle=_default_epsilon_angle):
        bravais_info = self._get_bravais_info(epsilon_angle=epsilon_angle,
                                              epsilon_length=epsilon_length)
        return bravais_info['extended_name']
    
    def get_special_points_relative(self,epsilon_length=_default_epsilon_length,epsilon_angle=_default_epsilon_angle):
        """
        Get the special point of a given structure.
        Coordinaets are based on the paper: arXiv:1004.2974, W. Setyawan, S. Curtarolo
        """
        import copy
        # recognize which bravais lattice we are dealing with
        bravais_info = self._get_bravais_info(epsilon_angle=epsilon_angle,
                                              epsilon_length=epsilon_length)
        
        # pick the information about the special k-points
        # simple cubic
        if bravais_info['index']==1:
            special_points = [{'label':'G','coordinates':[0., 0., 0. ]},
                              {'label':'M','coordinates':[0.5,0.5,0. ]},
                              {'label':'R','coordinates':[0.5,0.5,0.5]},
                              {'label':'X','coordinates':[0., 0.5,0. ]},
                              ]
                    
        # face centered cubic
        elif bravais_info['index']==2:
            special_points = [{'label':'G','coordinates':[0.,   0.,   0.   ]},
                              {'label':'K','coordinates':[3./8.,3./8.,0.75 ]},
                              {'label':'L','coordinates':[0.5,  0.5,  0.5  ]},
                              {'label':'U','coordinates':[5./8.,0.25, 5./8.]},
                              {'label':'W','coordinates':[0.5,  0.5,  0.75 ]},
                              {'label':'X','coordinates':[0.5,  0.,   0.5  ]},
                              ]

        # body centered cubic
        elif bravais_info['index']==3:
            special_points = [{'label':'G','coordinates':[0.,  0.,  0.  ]},
                              {'label':'H','coordinates':[0.5,-0.5, 0.5 ]},
                              {'label':'P','coordinates':[0.25,0.25,0.25]},
                              {'label':'N','coordinates':[0.,  0.,  0.5 ]},
                              ]

        # Tetragonal
        elif bravais_info['index'] == 4:
            special_points = [{'label':'G','coordinates':[0., 0., 0.  ]},
                              {'label':'A','coordinates':[0.5,0.5,0.5 ]},
                              {'label':'M','coordinates':[0.5,0.5,0.  ]},
                              {'label':'R','coordinates':[0., 0.5,0.5 ]},
                              {'label':'X','coordinates':[0., 0.5,0.  ]},
                              {'label':'Z','coordinates':[0., 0., 0.5 ]},
                              ]
            
        # body centered tetragonal
        elif bravais_info['index']==5:
            if bravais_info['variation']=='bct1':
                # Body centered tetragonal bct1
                eta = bravais_info['extra']['eta']
                special_points = [
                        {'label':'G' ,'coordinates':[0.,  0.,    0.   ]},
                        {'label':'M' ,'coordinates':[-0.5,0.5,   0.5  ]},
                        {'label':'N' ,'coordinates':[0.,  0.5,   0.   ]},
                        {'label':'P' ,'coordinates':[0.25,0.25,  0.25 ]},
                        {'label':'X' ,'coordinates':[0.,  0.,    0.5  ]},
                        {'label':'Z' ,'coordinates':[eta, eta,  -eta  ]},
                        {'label':'Z1','coordinates':[-eta,1.-eta,eta  ]},
                        ]
            else: # bct2
                # Body centered tetragonal bct2
                eta = bravais_info['extra']['eta']
                csi = bravais_info['extra']['csi']
                special_points = [
                        {'label':'G' ,'coordinates':[0.,  0.,   0.   ]},
                        {'label':'N' ,'coordinates':[0.,  0.5,  0.   ]},
                        {'label':'P' ,'coordinates':[0.25,0.25, 0.25 ]},
                        {'label':'S' ,'coordinates':[-eta,eta,  eta  ]},
                        {'label':'S1','coordinates':[eta, 1-eta,-eta ]},
                        {'label':'X' ,'coordinates':[0.,  0.,   0.5  ]},
                        {'label':'Y' ,'coordinates':[-csi,csi,  0.5  ]},
                        {'label':'Y1','coordinates':[0.5, 0.5, -csi  ]},
                        {'label':'Z' ,'coordinates':[0.5, 0.5, -0.5  ]},
                        ]

        # orthorhombic
        elif bravais_info['index'] == 6:
            special_points = [{'label':'G','coordinates':[0.,  0.,  0.  ]},
                              {'label':'R','coordinates':[0.5, 0.5, 0.5 ]},
                              {'label':'S','coordinates':[0.5, 0.5, 0.  ]},
                              {'label':'T','coordinates':[0.,  0.5, 0.5 ]},
                              {'label':'U','coordinates':[0.5, 0.,  0.5 ]},
                              {'label':'X','coordinates':[0.5, 0.,  0.  ]},
                              {'label':'Y','coordinates':[0.,  0.5, 0.  ]},
                              {'label':'Z','coordinates':[0.,  0.,  0.5 ]},
                              ]

        # face-centered orthorhombic
        elif bravais_info['index'] == 7:
            if bravais_info['variation']=='orcf1':
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                special_points = [
                              {'label':'G', 'coordinates':[0.,  0.,      0.  ]},
                              {'label':'A', 'coordinates':[0.5, 0.5+csi, csi ]},
                              {'label':'A1','coordinates':[0.5,0.5-csi,1.-csi]},
                              {'label':'L', 'coordinates':[0.5, 0.5,     0.5 ]},
                              {'label':'T', 'coordinates':[1.,  0.5,     0.5 ]},
                              {'label':'X', 'coordinates':[0.,  eta,     eta ]},
                              {'label':'X1','coordinates':[1., 1.-eta,1.-eta ]},
                              {'label':'Y', 'coordinates':[0.5, 0.,      0.5 ]},
                              {'label':'Z', 'coordinates':[0.5, 0.5,     0.  ]},
                              ]
            elif bravais_info['variation']=='orcf2':
                eta = bravais_info['extra']['eta']
                dlt = bravais_info['extra']['dlt']
                phi = bravais_info['extra']['phi']
                special_points = [
                              {'label':'G', 'coordinates':[0.,  0.,      0.  ]},
                              {'label':'C', 'coordinates':[0.5,0.5-eta,1.-eta]},
                              {'label':'C1','coordinates':[0.5,0.5+eta, eta  ]},
                              {'label':'D', 'coordinates':[0.5-dlt,0.5,1.-dlt]},
                              {'label':'D1','coordinates':[0.5+dlt,0.5, dlt  ]},
                              {'label':'L', 'coordinates':[0.5, 0.5,    0.5  ]},
                              {'label':'H', 'coordinates':[1.-phi,0.5-phi,0.5]},
                              {'label':'H1','coordinates':[phi,0.5+phi, 0.5  ]},
                              {'label':'X', 'coordinates':[0.,  0.5,    0.5  ]},
                              {'label':'Y', 'coordinates':[0.5, 0.,     0.5  ]},
                              {'label':'Z', 'coordinates':[0.5, 0.5,    0.   ]},
                              ]

            else:
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                special_points = [
                              {'label':'G', 'coordinates':[0.,  0.,      0.  ]},
                              {'label':'A', 'coordinates':[0.5, 0.5+csi, csi ]},
                              {'label':'A1','coordinates':[0.5,0.5-csi,1.-csi]},
                              {'label':'L', 'coordinates':[0.5, 0.5,     0.5 ]},
                              {'label':'T', 'coordinates':[1.,  0.5,     0.5 ]},
                              {'label':'X', 'coordinates':[0.,  eta,     eta ]},
                              {'label':'X1','coordinates':[1., 1.-eta,1.-eta ]},
                              {'label':'Y', 'coordinates':[0.5, 0.,      0.5 ]},
                              {'label':'Z', 'coordinates':[0.5, 0.5,     0.  ]},
                              ]

        # Body centered orthorhombic
        elif bravais_info['index']==8:
            csi = bravais_info['extra']['csi']
            dlt = bravais_info['extra']['dlt']
            eta = bravais_info['extra']['eta']
            mu  = bravais_info['extra']['mu']
            special_points = [{'label':'G', 'coordinates':[0.,   0.,   0.   ]},
                              {'label':'L', 'coordinates':[-mu,  mu, 0.5-dlt]},
                              {'label':'L1','coordinates':[mu,  -mu, 0.5+dlt]},
                              {'label':'L2','coordinates':[0.5-dlt,0.5+dlt,-mu]},
                              {'label':'R', 'coordinates':[0.,  0.5,   0.   ]},
                              {'label':'S', 'coordinates':[0.5,  0.,   0.   ]},
                              {'label':'T', 'coordinates':[0.,   0.,   0.5  ]},
                              {'label':'W', 'coordinates':[0.25,0.25,  0.25 ]},
                              {'label':'X', 'coordinates':[-csi, csi,  csi  ]},
                              {'label':'X1','coordinates':[csi,1.-csi,-csi  ]},
                              {'label':'Y', 'coordinates':[eta, -eta,  eta  ]},
                              {'label':'Y1','coordinates':[1.-eta, eta,-eta ]},
                              {'label':'Z', 'coordinates':[0.5,  0.5,  -0.5 ]},
                              ]

        # C-centered orthorhombic
        elif bravais_info['index']==9:
            csi = bravais_info['extra']['csi']
            special_points = [{'label':'G', 'coordinates':[0.,  0.,     0.  ]},
                              {'label':'A', 'coordinates':[csi, csi,    0.5 ]},
                              {'label':'A1','coordinates':[-csi,1.-csi, 0.5 ]},
                              {'label':'R', 'coordinates':[0.,  0.5,    0.5 ]},
                              {'label':'S', 'coordinates':[0.,  0.5,    0.  ]},
                              {'label':'T', 'coordinates':[-0.5,0.5,    0.5 ]},
                              {'label':'X', 'coordinates':[csi, csi,    0.  ]},
                              {'label':'X1','coordinates':[-csi,1.-csi, 0.  ]},
                              {'label':'Y', 'coordinates':[-0.5,0.5,    0.  ]},
                              {'label':'Z', 'coordinates':[0.,  0.,     0.5 ]},
                              ]

        # Hexagonal
        elif bravais_info['index']==10:
            special_points = [{'label':'G','coordinates':[0.,   0.,   0. ]},
                              {'label':'A','coordinates':[0.,   0.,   0.5]},
                              {'label':'H','coordinates':[1./3.,1./3.,0.5]},
                              {'label':'K','coordinates':[1./3.,1./3.,0. ]},
                              {'label':'L','coordinates':[0.5,  0.,   0.5]},
                              {'label':'M','coordinates':[0.5,  0.,   0. ]},
                              ]

        # rhombohedral
        elif bravais_info['index']==11:
            if bravais_info['variation']=='rhl1':
                eta = bravais_info['extra']['eta']
                nu  = bravais_info['extra']['nu']
                special_points = [
                              {'label':'G', 'coordinates':[0.,   0.,    0.  ]},
                              {'label':'B', 'coordinates':[eta, 0.5,1.-eta  ]},
                              {'label':'B1','coordinates':[0.5,1.-eta,eta-1.]},
                              {'label':'F', 'coordinates':[0.5, 0.5,    0.  ]},
                              {'label':'L', 'coordinates':[0.5,  0.,    0.  ]},
                              {'label':'L1','coordinates':[0. ,  0.,   -0.5 ]},
                              {'label':'P', 'coordinates':[eta,  nu,    nu  ]},
                              {'label':'P1','coordinates':[1.-nu,1.-nu,1.-eta]},
                              {'label':'P2','coordinates':[nu,   nu, eta-1. ]},
                              {'label':'Q', 'coordinates':[1.-nu,nu,    0.  ]},
                              {'label':'X', 'coordinates':[nu,   0.,   -nu  ]},
                              {'label':'Z', 'coordinates':[0.5,  0.5,   0.5 ]},
                              ]
            else: # Rhombohedral rhl2
                eta = bravais_info['extra']['eta']
                nu  = bravais_info['extra']['nu']
                special_points = [
                              {'label':'G', 'coordinates':[0.,     0.,   0.  ]},
                              {'label':'F', 'coordinates':[0.5,  -0.5,   0.  ]},
                              {'label':'L', 'coordinates':[0.5,    0.,   0.  ]},
                              {'label':'P', 'coordinates':[1.-nu,-nu,1. -nu  ]},
                              {'label':'P1','coordinates':[nu,  nu-1.,  nu-1.]},
                              {'label':'Q', 'coordinates':[eta,   eta,   eta ]},
                              {'label':'Q1','coordinates':[1.-eta,-eta, -eta ]},
                              {'label':'Z', 'coordinates':[0.5,  -0.5,   0.5]},
                              ]
    
        # monoclinic
        elif bravais_info['index']==12:
            eta = bravais_info['extra']['eta']
            nu = bravais_info['extra']['nu']
            special_points = [{'label':'G', 'coordinates':[ 0.,   0.,   0.  ]},
                              {'label':'A', 'coordinates':[0.5,  0.5,   0.  ]},
                              {'label':'C', 'coordinates':[ 0.,  0.5,   0.5 ]},
                              {'label':'D', 'coordinates':[0.5,   0.,   0.5 ]},
                              {'label':'D1','coordinates':[0.5,   0.,  -0.5 ]},
                              {'label':'E', 'coordinates':[0.5,  0.5,   0.5 ]},
                              {'label':'H', 'coordinates':[ 0.,  eta, 1.-nu ]},
                              {'label':'H1','coordinates':[ 0.,1.-eta,  nu  ]},
                              {'label':'H2','coordinates':[ 0.,  eta,  -nu  ]},
                              {'label':'M', 'coordinates':[0.5,  eta, 1.-nu ]},
                              {'label':'M1','coordinates':[0.5,1.-eta,  nu  ]},
                              {'label':'M2','coordinates':[0.5,  eta,  -nu  ]},
                              {'label':'X', 'coordinates':[ 0.,  0.5,   0.  ]},
                              {'label':'Y', 'coordinates':[ 0.,   0.,   0.5 ]},
                              {'label':'Y1','coordinates':[ 0.,   0.,  -0.5 ]},
                              {'label':'Z', 'coordinates':[0.5,   0.,   0.  ]},
                              ]

        elif bravais_info['index'] == 13:
            if bravais_info['variation']=='mclc1':
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                psi = bravais_info['extra']['psi']
                phi = bravais_info['extra']['phi']
                special_points = [
                              {'label':'G', 'coordinates':[ 0.,   0.,   0.  ]},
                              {'label':'N', 'coordinates':[0.5,   0.,   0.  ]},
                              {'label':'N1','coordinates':[ 0., -0.5,   0.  ]},
                              {'label':'F', 'coordinates':[1.-csi,1.-csi,1.-eta]},
                              {'label':'F1','coordinates':[  csi,  csi,   eta]},
                              {'label':'F2','coordinates':[  csi, -csi,1.-eta]},
                              {'label':'F3','coordinates':[1.-csi,-csi,1.-eta]},
                              {'label':'I', 'coordinates':[  phi, 1.-phi, 0.5]},
                              {'label':'I1','coordinates':[1.-phi, phi-1.,0.5]},
                              {'label':'L', 'coordinates':[ 0.5,    0.5,  0.5]},
                              {'label':'M', 'coordinates':[ 0.5,     0.,  0.5]},
                              {'label':'X', 'coordinates':[1.-psi,psi-1., 0. ]},
                              {'label':'X1','coordinates':[psi,  1.-psi,  0. ]},
                              {'label':'X2','coordinates':[psi-1., -psi,  0. ]},
                              {'label':'Y', 'coordinates':[ 0.5,    0.5,  0. ]},
                              {'label':'Y1','coordinates':[-0.5,   -0.5,  0. ]},
                              {'label':'Z', 'coordinates':[0.,       0.,  0.5]},
                              ]
            elif bravais_info['variation']=='mclc2':
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                psi = bravais_info['extra']['psi']
                phi = bravais_info['extra']['phi']
                special_points = [
                              {'label':'G', 'coordinates':[ 0.,   0.,   0.  ]},
                              {'label':'N', 'coordinates':[0.5,   0.,   0.  ]},
                              {'label':'N1','coordinates':[ 0., -0.5,   0.  ]},
                              {'label':'F', 'coordinates':[1.-csi,1.-csi,1.-eta]},
                              {'label':'F1','coordinates':[  csi,  csi,   eta]},
                              {'label':'F2','coordinates':[  csi, -csi,1.-eta]},
                              {'label':'F3','coordinates':[1.-csi,-csi,1.-eta]},
                              {'label':'I', 'coordinates':[  phi, 1.-phi, 0.5]},
                              {'label':'I1','coordinates':[1.-phi, phi-1.,0.5]},
                              {'label':'L', 'coordinates':[ 0.5,    0.5,  0.5]},
                              {'label':'M', 'coordinates':[ 0.5,     0.,  0.5]},
                              {'label':'X', 'coordinates':[1.-psi,psi-1., 0. ]},
                              {'label':'X1','coordinates':[psi,  1.-psi,  0. ]},
                              {'label':'X2','coordinates':[psi-1., -psi,  0. ]},
                              {'label':'Y', 'coordinates':[ 0.5,    0.5,  0. ]},
                              {'label':'Y1','coordinates':[-0.5,   -0.5,  0. ]},
                              {'label':'Z', 'coordinates':[0.,       0.,  0.5]},
                              ]
            elif bravais_info['variation']=='mclc3':
                mu  = bravais_info['extra']['mu']
                dlt = bravais_info['extra']['dlt']
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                phi = bravais_info['extra']['phi']
                psi = bravais_info['extra']['psi']
                special_points = [
                              {'label':'G', 'coordinates':[  0.,   0.,  0.   ]},
                              {'label':'F', 'coordinates':[1.-phi,1-phi,1.-psi]},
                              {'label':'F1','coordinates':[ phi,phi-1., psi  ]},
                              {'label':'F2','coordinates':[1.-phi,-phi,1.-psi]},
                              {'label':'H', 'coordinates':[ csi,  csi,  eta  ]},
                              {'label':'H1','coordinates':[1.-csi,-csi,1.-eta]},
                              {'label':'H2','coordinates':[-csi, -csi, 1.-eta]},
                              {'label':'I', 'coordinates':[ 0.5, -0.5,  0.5  ]},
                              {'label':'M', 'coordinates':[ 0.5,   0.,  0.5  ]},
                              {'label':'N', 'coordinates':[ 0.5,   0.,  0.   ]},
                              {'label':'N1','coordinates':[ 0. , -0.5,  0.   ]},
                              {'label':'X', 'coordinates':[ 0.5, -0.5,  0.   ]},
                              {'label':'Y', 'coordinates':[ mu ,   mu,  dlt  ]},
                              {'label':'Y1','coordinates':[1.-mu, -mu, -dlt  ]},
                              {'label':'Y2','coordinates':[-mu ,  -mu, -dlt  ]},
                              {'label':'Y3','coordinates':[ mu ,mu-1.,  dlt  ]},
                              {'label':'Z', 'coordinates':[ 0. ,   0.,  0.5  ]},
                              ]
            elif bravais_info['variation']=='mclc4':
                mu  = bravais_info['extra']['mu']
                dlt = bravais_info['extra']['dlt']
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                phi = bravais_info['extra']['phi']
                psi = bravais_info['extra']['psi']
                special_points = [
                              {'label':'G', 'coordinates':[  0.,   0.,  0.   ]},
                              {'label':'F', 'coordinates':[1.-phi,1-phi,1.-psi]},
                              {'label':'F1','coordinates':[ phi,phi-1., psi  ]},
                              {'label':'F2','coordinates':[1.-phi,-phi,1.-psi]},
                              {'label':'H', 'coordinates':[ csi,  csi,  eta  ]},
                              {'label':'H1','coordinates':[1.-csi,-csi,1.-eta]},
                              {'label':'H2','coordinates':[-csi, -csi, 1.-eta]},
                              {'label':'I', 'coordinates':[ 0.5, -0.5,  0.5  ]},
                              {'label':'M', 'coordinates':[ 0.5,   0.,  0.5  ]},
                              {'label':'N', 'coordinates':[ 0.5,   0.,  0.   ]},
                              {'label':'N1','coordinates':[ 0. , -0.5,  0.   ]},
                              {'label':'X', 'coordinates':[ 0.5, -0.5,  0.   ]},
                              {'label':'Y', 'coordinates':[ mu ,   mu,  dlt  ]},
                              {'label':'Y1','coordinates':[1.-mu, -mu, -dlt  ]},
                              {'label':'Y2','coordinates':[-mu ,  -mu, -dlt  ]},
                              {'label':'Y3','coordinates':[ mu ,mu-1.,  dlt  ]},
                              {'label':'Z', 'coordinates':[ 0. ,   0.,  0.5  ]},
                              ]
            else:
                csi = bravais_info['extra']['csi']
                mu  = bravais_info['extra']['mu']
                omg = bravais_info['extra']['omg']
                eta = bravais_info['extra']['eta']
                nu  = bravais_info['extra']['nu']
                dlt = bravais_info['extra']['dlt']
                rho = bravais_info['extra']['rho']
                special_points = [
                              {'label':'G', 'coordinates':[  0.,   0.,  0.   ]},
                              {'label':'F', 'coordinates':[  nu,   nu,  omg  ]},
                              {'label':'F1','coordinates':[1.-nu,1.-nu,1.-omg]},
                              {'label':'F2','coordinates':[  nu, nu-1., omg  ]},
                              {'label':'H', 'coordinates':[ csi,  csi,  eta  ]},
                              {'label':'H1','coordinates':[1.-csi,-csi,1.-eta]},
                              {'label':'H2','coordinates':[-csi, -csi, 1.-eta]},
                              {'label':'I', 'coordinates':[rho,1.-rho,  0.5  ]},
                              {'label':'I1','coordinates':[1.-rho,rho-1.,0.5]},
                              {'label':'L', 'coordinates':[ 0.5,  0.5,  0.5  ]},
                              {'label':'M', 'coordinates':[ 0.5,  0.,   0.5]},
                              {'label':'N', 'coordinates':[ 0.5,  0.,   0.   ]},
                              {'label':'N1','coordinates':[ 0.,  -0.5,  0.   ]},
                              {'label':'X', 'coordinates':[ 0.5, -0.5,  0.   ]},
                              {'label':'Y', 'coordinates':[ mu ,   mu,  dlt  ]},
                              {'label':'Y1','coordinates':[1.-mu, -mu, -dlt  ]},
                              {'label':'Y2','coordinates':[-mu ,  -mu, -dlt  ]},
                              {'label':'Y3','coordinates':[ mu ,mu-1.,  dlt  ]},
                              {'label':'Z', 'coordinates':[ 0. ,   0.,  0.5  ]},
                              ]
            
        if bravais_info['index']==14:
            if bravais_info['variation']=='tri1a' or bravais_info['variation']=='tri2a':
                special_points = [
                              {'label':'G','coordinates':[ 0.0, 0.0, 0.0 ]},
                              {'label':'L','coordinates':[ 0.5, 0.5, 0.0 ]},
                              {'label':'M','coordinates':[ 0.0, 0.5, 0.5 ]},
                              {'label':'N','coordinates':[ 0.5, 0.0, 0.5 ]},
                              {'label':'R','coordinates':[ 0.5, 0.5, 0.5 ]},
                              {'label':'X','coordinates':[ 0.5, 0.0, 0.0 ]},
                              {'label':'Y','coordinates':[ 0.0, 0.5, 0.0 ]},
                              {'label':'Z','coordinates':[ 0.0, 0.0, 0.5 ]},
                              ]
            else:
                special_points = [
                              {'label':'G','coordinates':[ 0.0, 0.0, 0.0 ]},
                              {'label':'L','coordinates':[ 0.5,-0.5, 0.0 ]},
                              {'label':'M','coordinates':[ 0.0, 0.0, 0.5 ]},
                              {'label':'N','coordinates':[-0.5,-0.5, 0.5 ]},
                              {'label':'R','coordinates':[ 0.0,-0.5, 0.5 ]},
                              {'label':'X','coordinates':[ 0.0,-0.5, 0.0 ]},
                              {'label':'Y','coordinates':[ 0.5, 0.0, 0.0 ]},
                              {'label':'Z','coordinates':[-0.5, 0.0, 0.5 ]},
                              ]            

        permutation = bravais_info['permutation']

        def permute(x,permutation):
            if permutation==[0,1,2]:
                return [ x[0],x[1],x[2] ]
            elif permutation==[0,2,1]:
                return [ x[0],x[2],x[1] ]
            elif permutation==[1,0,2]:
                return [ x[1],x[0],x[2] ]
            elif permutation==[1,2,0]:
                return [ x[1],x[2],x[0] ]
            elif permutation==[2,0,1]:
                return [ x[2],x[0],x[1] ]
            else: # permutation==[2,1,0]:
                return [ x[2],x[1],x[0] ]

        the_special_points = []
        for i in special_points:
            a = copy.copy(i)
            a['coordinates'] = permute(i['coordinates'],permutation)
            the_special_points.append(a)

        return the_special_points






