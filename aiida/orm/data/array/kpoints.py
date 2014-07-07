# -*- coding: utf-8 -*-
"""
This module defines the classes related to band structures or dispersions
in a Brillouin zone, and how to operate on them.
"""

from aiida.orm.data.array import ArrayData
import copy
import numpy
from aiida.common.utils import classproperty

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = "Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

class KpointsData(ArrayData):
    
    # Default values to be set for new nodes
    @classproperty
    def _set_defaults(cls):
        return {"labels": [],
          }

    @property
    def labels(self):
        """
        Get the labels of the kpoints
        """
        labels = self.get_attr('labels')
        label_numbers = self.get_attr('label_numbers')
        return tuple(zip(label_numbers,labels))

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

    def set_from_structure(self,StructureData,pbc=None):
        cell = StructureData.cell
        if pbc is None:
            pbc = StructureData.pbc
        self.set_from_real_cell(cell,pbc)
    
    def set_from_real_cell(self,cell,pbc=[True,True,True]):
        """
        "param cell: 3x3 matrix of cell vectors. Orientation: each row 
                     represent a lattice vector
        :param pbc: list of 3 booleans, True if in the first lattice vector
                    direction, there is periodicity.
        """
        self._set_real_cell(cell)
        self.set_pbc(pbc)
        self._set_reciprocal_cell()

    def _set_reciprocal_cell(self):
        """
        Creates the reciprocal cell, which is a dim x dim matrix.
        The reciprocal cell internally stored is always rotated so that:
        a) the  
        """
        if self.dimension==0:
            raise NotImplementedError
            self.set_attr('reciprocal_cell',None)
            self.set_attr('transformation_matrix',None)
            return
        
        # construct the direct_cell, where only periodic vectors are considered
        # i.e. a dim x dim matrix
        direct_cell = numpy.array(self.real_cell) # a 3x3 matrix !
        reciprocal_cell_3 = 2.*numpy.pi*numpy.linalg.inv(direct_cell) # 3x3 rec cell

        # INTERNALLY I USE THE TRANSPOSE MATRIX! easier for transformations
        # i.e. columns are the lattice vectors
        
        # rotate the direct cell to an upper triangular matrix,
        # i.e. the lattice vector a1 is on (1,0,0), a2 is in the plane xy
        # Note: the matrix is acting on the transpose
        upper_tr_rec_cell,left_matrix,right_matrix = self._transform_to_uppertr(
                                                            reciprocal_cell_3.T) 
        # transpose it back. Remember that left and right matrix will act on the transpose only!
        upper_tr_rec_cell = upper_tr_rec_cell.T
        
        # reduce the direct 3x3 matrix to a dim x dim matrix
        rec_cell = self._reduce_matrix_dimension(upper_tr_rec_cell)

        self.set_attr('reciprocal_cell',rec_cell)
        self.set_attr('rotated_rec_cell_3',upper_tr_rec_cell)
        self.set_attr('left_matrix',left_matrix)
        self.set_attr('right_matrix',right_matrix)
        self.set_attr('reciprocal_cell_3',reciprocal_cell_3)
        
    def _reduce_matrix_dimension(self,matrix):
        output = copy.deepcopy(matrix)
        row_col_to_delete = range(2,self.dimension-1,-1)
        for i in row_col_to_delete: # from the last one to preserve indeces
            output = numpy.delete(output,i,axis=0)
            output = numpy.delete(output,i,axis=1)
        return output
        
    def _transform_to_uppertr(self,in_mat):
        """
        Takes in input a 3x3 matrix in_mat and the periodicities.
        Each column is a vector.
        Rotates it so that non periodic vectors are on the left
        Returns the rotated matrix and the transformation matrix 
        """
        # first we apply the permutation
        
        # start with the identity
        right_matrix = numpy.eye(3)
        permuted_mat = copy.copy(in_mat)

        # First permute the indices, so that the first n="dimension" rows are periodic        
        pbc = self.pbc
        for i,periodic in enumerate(pbc):
            if not periodic:
                for j in range(i+1,3):
                    if pbc[j]: # switch only False periodic with True periodic
                        # multiply on the left the matrix
                        permuted_mat,perm_matrix = _return_permutation_matrix(permuted_mat,i,j)
                        right_matrix = numpy.dot(right_matrix,perm_matrix)
        
        # first we align the first column with the x axis
        v1 = permuted_mat[:,0]
        #v2 = permuted_mat[:,1]
        v1len = numpy.linalg.norm(v1)

        # angle between v1 and the x axis
        cosphi = v1[0]/v1len
        sinphi = numpy.sqrt(1.-cosphi**2)
        
        # this is v1 [cross] x
        rotaxis = numpy.cross(v1,[1,0,0]) 
        rotaxislen = numpy.linalg.norm(rotaxis)
        
        if rotaxislen == 0: # matrix already aligned with x
            Qx = numpy.eye(3)
        else:
            x, y, z = rotaxis / rotaxislen
            Qx = numpy.array([[x**2*(1.-cosphi) + cosphi, 
                               x*y *(1.-cosphi) - z*sinphi, 
                               x*z *(1.-cosphi) + y*sinphi ],
                              [x*y *(1.-cosphi) + z*sinphi,
                               y**2*(1.-cosphi) + cosphi,
                               y*z *(1.-cosphi) - x*sinphi ],
                              [x*z *(1.-cosphi) - y*sinphi,
                               y*z *(1.-cosphi) + x*sinphi,
                               z**2*(1.-cosphi) + cosphi   ],
                             ]
                            )
        
        # then we move the second axis in the plane xy
        after_x = numpy.dot(Qx,permuted_mat)
        # this is the v2 after the rotation        
        rot_v2 = after_x[:,1]
        #rot_v2len = numpy.linalg.norm(rot_v2)
        
        rot_v2_proj = numpy.array([0.,rot_v2[1],rot_v2[2]])
        rot_v2proj_len = numpy.linalg.norm(rot_v2_proj)
        cosphi = numpy.dot(rot_v2_proj,[0.,1.,0.]) /rot_v2proj_len 
        sinphi = numpy.sqrt(1.-cosphi**2)
        
        # i.e. we rotate around the axis x
        rotaxis = numpy.cross(rot_v2_proj,[0,1,0]) 
        rotaxislen = numpy.linalg.norm(rotaxis)

        if rotaxislen==0:
            Qxy=numpy.eye(3)
        else:
            x, y, z = rotaxis / rotaxislen
            Qxy = numpy.array([[x**2*(1.-cosphi) + cosphi, 
                            x*y *(1.-cosphi) - z*sinphi, 
                            x*z *(1.-cosphi) + y*sinphi ],
                           [x*y *(1.-cosphi) + z*sinphi,
                            y**2*(1.-cosphi) + cosphi,
                            y*z *(1.-cosphi) - x*sinphi ],
                           [x*z *(1.-cosphi) - y*sinphi,
                            y*z *(1.-cosphi) + x*sinphi,
                            z**2*(1.-cosphi) + cosphi   ],
                           ]
                          )
        
        left_matrix = numpy.dot(Qxy, Qx)
        upper_tr = numpy.dot(Qxy,after_x)
        
        return upper_tr, left_matrix, right_matrix
            
    @property
    def dimension(self):
        """
        Get the periodic boundary conditions.
        
        :return: dimensionality number (from 0 to 3)
        """
        #return copy.deepcopy(self._pbc)
        return self.get_attr('dimension')

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
        from aiida.orm.data.structure import _get_valid_pbc #TODO: this is not good to do!

        if not self._to_be_stored:
            raise ModificationNotAllowed(
                            "The BandsData object cannot be modified, "
                            "it has already been stored")
        the_pbc = _get_valid_pbc(value)
        self.set_attr('pbc1',the_pbc[0])
        self.set_attr('pbc2',the_pbc[1])
        self.set_attr('pbc3',the_pbc[2])
        self.set_attr('dimension',the_pbc.count(True))

    @property
    def real_cell(self):
        """
        Returns the cell shape.
        
        :return: a 3x3 list of lists.
        """
        return copy.deepcopy(self.get_attr('real_cell'))
    
    # this is a hidden function, one could change the real cell,
    # after the brillouin zone is set! 
    def _set_real_cell(self, value):
        from aiida.common.exceptions import ModificationNotAllowed
        from aiida.orm.data.structure import _get_valid_cell
        if not self._to_be_stored:
            raise ModificationNotAllowed(
                "The BandsData object cannot be modified, "
                "it has already been stored")

        the_cell = _get_valid_cell(value)
        self.set_attr('real_cell', the_cell)
        
    def get_reciprocal_cell(self,rotated=True,reduced_dimension=True):
        """
        Return the reciprocal lattice cell.
        """
        if not rotated:
            left = numpy.linalg.inv(self.get_attr('left_matrix'))
        
        if reduced_dimension:
            if rotated:
                return self.get_attr('reciprocal_cell')
            else:
                upper_tr =  self.get_attr('rotated_rec_cell_3')
                non_rot = numpy.dot(left,upper_tr.T).T
                non_rot = self._reduce_matrix_dimension(non_rot)
                return non_rot
        else:
            if rotated:
                return self.get_attr('rotated_rec_cell_3')
            else:
                return self.get_attr('reciprocal_cell_3')
          
    def set_kpoints_absolute(self,kpoints,weights=None):
        """
        Absolute points, but in the carthesian dim x dim basis, where the 
        dim x dim reciprocal cell is located. 
        """
        try:
            _=self.get_attr('reciprocal_cell')
        except AttributeError:
            raise ValueError("Trying to set the kpoints without setting up the "
                             "the reciprocal cell")
        
        # validate input
        the_kpoints,the_weights = _validate_kpoints_weights(kpoints,weights)
        
        if the_kpoints.shape[1] != self.dimension:
            raise ValueError("In a system which has {} dimensions, kpoint need"
                             "only {} coordinates".format(self.dimension,self.dimension))
        
        # pad the kpoints until we have three coodrdinates
        while the_kpoints.shape[1] < 3:
            new_col = numpy.zeros((the_kpoints.shape[0],1))
            the_kpoints = numpy.append(the_kpoints,new_col,1)
        
        right = self.get_attr('right_matrix')
        left = self.get_attr('left_matrix')
        
        # apply the permutations
        the_kpoints = numpy.dot(the_kpoints,right) # I can avoid the transposed  kpoints
        
        # put them in the rotated basis
        the_kpoints = numpy.dot(left,the_kpoints.T).T
        
        # drop the non periodic coordinates
        row_col_to_delete = range(2,self.dimension-1,-1)
        for i in row_col_to_delete: # from the last one to preserve indeces
            the_kpoints = numpy.delete(the_kpoints,i,axis=1)
  
        # scale them to relative coordinates
        rec_cell = self.get_reciprocal_cell(rotated=True,reduced_dimension=True)
        the_kpoints = numpy.dot(rec_cell,the_kpoints.T).T
        # the_kpoints are a matrix [N x dim]
        
        # store
        self.set_array('kpoints',the_kpoints)
        self.set_array('weights',the_weights)
        
        
    def get_kpoints_absolute(self,rotated=True,
                                also_weights=False,
                                zero_padding=False):
        """
        Get the carthesian coordinates of the kpoints.
        If rotated=True, rotates the absolute coordinates so that they are 
        aligned with the reciprocal cell of the initial structure.
        if reduced_dimension = True, prints the kpoints with (dim) coordinates.
        """
        kpoints = numpy.array(self.get_array('kpoints'))
        weights = numpy.array(self.get_array('weights'))
        
        # kpoints with dim coordinates, in the rotated frame
        if not zero_padding and rotated:
            rec_cell = self.get_reciprocal_cell(reduced_dimension=True,
                                                rotated=False)
            kpoints = numpy.dot(numpy.linalg.inv(rec_cell),kpoints.T).T
        
        # kpoints with dim coordinates, in the rotated frame
        if not zero_padding and not rotated:
            if self.dimension != 3:
                raise NotImplementedError("not zero padding, and not rotated case "
                                      "is not implemented for lower dimensionality")
                # actually, I'm not sure of the physical meaning of this
            else:
                rec_cell = self.get_reciprocal_cell(rotated=False)
                kpoints = numpy.dot(numpy.linalg.inv(rec_cell),kpoints.T).T
                
        if zero_padding:
            # pad the kpoints until we have three coodrdinates
            while kpoints.shape[1] < 3:
                new_col = numpy.zeros((kpoints.shape[0],1))
                kpoints = numpy.append(kpoints,new_col,1)
            
            if not rotated:
                rec_cell = self.get_reciprocal_cell(reduced_dimension=False,
                                                    rotated=False)
            else:
                rec_cell = self.get_reciprocal_cell(reduced_dimension=False,
                                                    rotated=True)                
            kpoints = numpy.dot(numpy.linalg.inv(rec_cell),kpoints.T).T

        # return
        if also_weights:
            return kpoints,weights
        else:
            return kpoints
        

    def set_kpoints_relative(self,kpoints,weights=None):
        """
        In units of the #dim reciprocal lattice vectors.
        A list of kpoints, each kpoint being a list of [dim] coordinates
        """
        # check that it is a 'dim'x #kpoints dimensional array
        the_kpoints,the_weights = _validate_kpoints_weights(kpoints,weights)
        
        if the_kpoints.shape[1] != self.dimension:
            raise ValueError("In a system which has {} dimensions, kpoint need"
                             "only {} coordinates".format(self.dimension,self.dimension))
        # store
        self.set_array('kpoints',the_kpoints)
        self.set_array('weights',the_weights)
        
    def get_kpoints_relative(self,zero_padding=False,also_weights=False):
        """
        get the kpoints in units of the dim reciprocal lattice vectors.
        """
        kpoints = numpy.array(self.get_array('kpoints'))
        weights = numpy.array(self.get_array('weights'))
        if zero_padding:
            while kpoints.shape[1] < 3:
                new_col = numpy.zeros((kpoints.shape[0],1))
                kpoints= numpy.append(kpoints,new_col,1)
        if also_weights:
            return kpoints,weights
        else:
            return kpoints
    
    def get_weights(self):
        return self.get_array('weights')

def _validate_kpoints_weights(kpoints,weights):
    kpoints = numpy.array(kpoints)
    if weights is None:
        weights = numpy.ones((kpoints.shape[0]))
    else:
        weights = numpy.array(weights)
        if len(weights) != kpoints.shape[0]:
            raise ValueError("Found {} weights but {} kpoints"
                             .format(len(weights), len(kpoints)))
        
    if kpoints.dtype != numpy.dtype(numpy.float):
        raise ValueError("kpoints must be an array of type floats. "
                         "Found instead {}".format(kpoints.dtype))
    if weights.dtype != numpy.dtype(numpy.float):
        raise ValueError("weights must be an array of type floats. "
                         "Found instead {}".format(weights.dtype))
    return kpoints,weights

    
def _switch_columns(a,i,j):
    """
    Switch the rows i and j of matrix a
    Returns a new numpy.array
    """
    tmp = copy.copy(a)
    tmp[:,j] = a[:,i]
    tmp[:,i] = a[:,j]
    return tmp

def _return_permutation_matrix(a,i,j):
    """
    Returns the permutation of column i with j, and the transformation matrix
    t such that t x mat(non permutated) = mat(permutated) 
    """
    # hard code all possible permutation in 3x3 matrices
    if i==j:
        t =numpy.eye((3))
    # column permutations. rows should be the same, but acting on the left
    if (i==1 and j==2) or (i==2 and j==1):
        t = numpy.array([[1.,0.,0.],[0.,0.,1.],[0.,1.,0.]]) 
    if (i==0 and j==1) or (i==1 and j==0):
        t = numpy.array([[0.,1.,0.],[1.,0.,0.],[0.,0.,1.]]) 
    if (i==0 and j==2) or (i==2 and j==0):
        t = numpy.array([[0.,0.,1.],[0.,1.,0.],[1.,0.,0.]]) 
    b = _switch_columns(a,i,j)
    return b,t
