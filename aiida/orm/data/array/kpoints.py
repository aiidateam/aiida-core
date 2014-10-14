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

class KpointsData(ArrayData):

    def __init__(self,*args,**kwargs):
        super(KpointsData, self).__init__(*args, **kwargs)
        try:
            self._load_cell_properties()
        except AttributeError:
            pass
        
    @property
    def cell(self):
        """
        The crystal unit cell. Rows are the crystal vectors.
        :return: a 3x3 numpy.array
        """
        return numpy.array(self.get_attr('cell'))
        
    @cell.setter
    def cell(self,value):
        """
        Set the crystal unit cell
        :param value: a 3x3 list/tuple/array of numbers
        """
        self._set_cell(value)
        
    def _set_cell(self,value):
        """
        Validate if 'value' is a allowed crystal unit cell
        :param value: something compatible with a 3x3 tuple of floats
        """
        from aiida.common.exceptions import ModificationNotAllowed
        from aiida.orm.data.structure import _get_valid_cell
        if not self._to_be_stored:
            raise ModificationNotAllowed(
                "KpointsData cannot be modified, "
                "it has already been stored")
        
        the_cell = _get_valid_cell(value)

        self.set_attr('cell',the_cell)
        
    @property
    def bravais_lattice(self):
        """
        The dictionary containing informations about the cell symmetry
        """
        return self.get_attr('bravais_lattice')
        
    @bravais_lattice.setter
    def bravais_lattice(self,value):
        """
        Set the bravais lattice dictionary
        """
        self._set_bravais_lattice(value)
        
    def _set_bravais_lattice(self,value):
        """
        Validating function to set the bravais_lattice dictionary
        """
        import copy
        if not isinstance(value,dict):
            raise ValueError("bravais_lattice is not a dict")
        if not all( [ value.has_key(i) for i in ["short_name","extended_name","index","permutation"] ] ):
            raise ValueError()

        bravais_lattice = copy.copy(value)
        bravais_lattice['permutation'] = [ float(i) for i in value['permutation'] ]
        
        try:
            if not isinstance(bravais_lattice['variation'],str):
                raise ValueError()
        except KeyError:
            pass
        try:
            if not isinstance(bravais_lattice['extra'],dict):
                raise ValueError()
            if not all( [isinstance(i,float) for i in bravais_lattice['extra'].values()] ):
                raise ValueError()
        except KeyError:
            pass
            
        self.set_attr('bravais_lattice',bravais_lattice)
    
    def _get_or_create_bravais_lattice(self):
        """
        Try to get the bravais_lattice info if stored already, otherwise analyze
        the cell with the default settings and save this in the attribute.
        
        :return bravais_lattice: the dictionary containing the symmetry info
        """
        try:
            bravais_lattice = self.bravais_lattice
        except AttributeError:
            bravais_lattice = self._find_bravais_info()
            self.bravais_lattice = bravais_lattice
        return bravais_lattice
    
    @property
    def pbc(self):
        """
        The periodic boundary conditions along the vectors a1,a2,a3.
        
        :return: a tuple of three booleans, each one tells if there are periodic
            boundary conditions for the i-th real-space direction (i=1,2,3)
        """
        #return copy.deepcopy(self._pbc)
        return (self.get_attr('pbc1'),self.get_attr('pbc2'),self.get_attr('pbc3'))

    @pbc.setter
    def pbc(self,value):
        """
        Set the value of pbc, i.e. a tuple of three booleans, indicating if the
        cell is periodic in the 1,2,3 crystal direction
        """
        self._set_pbc(value)

    def _set_pbc(self, value):
        """
        validate the pbc, then store them
        """
        from aiida.common.exceptions import ModificationNotAllowed
        from aiida.orm.data.structure import get_valid_pbc

        if not self._to_be_stored:
            raise ModificationNotAllowed(
                            "The KpointsData object cannot be modified, "
                            "it has already been stored")
        the_pbc = get_valid_pbc(value)
        self.set_attr('pbc1',the_pbc[0])
        self.set_attr('pbc2',the_pbc[1])
        self.set_attr('pbc3',the_pbc[2])

    @property
    def labels(self):
        """
        Labels associated with the list of kpoints.
        List of tuples with kpoint index and kpoint name: [(0,'G'),(13,'M'),...]
        """
        label_numbers = self.get_attr('label_numbers',None)
        labels = self.get_attr('labels',None)
        if labels is None or label_numbers is None:
            return None
        return zip(label_numbers,labels)

    @labels.setter
    def labels(self,value): 
        self._set_labels(value)

    def _set_labels(self,value):
        """
        set label names. Must pass in input a list like: [[0,'X'],[34,'L'],... ]
        """
        # check if kpoints were set
        try:
            self.get_kpoints()
        except AttributeError:
            raise AttributeError("Kpoints must be set before the labels")
        
        try:
            label_numbers = [int(i[0]) for i in value]
        except ValueError:
            raise ValueError("The input must contain an integer index, to map"
                             " the labels into the kpoint list")
        labels = [str(i[1]) for i in value]
        
        if any( [i>len(self.get_kpoints())-1 for i in label_numbers]):
            raise ValueError("Index of label exceeding the list of kpoints")
        
        self.set_attr('label_numbers',label_numbers)
        self.set_attr('labels',labels)
        
# I commented this part, which atm I would leave it up to the user to set 
# new labels every time he modifies them. Anyway, labels should be set more 
# often by the set_path function
#     def append_label(self,value):
#         """
#         Add a label to the existing ones.
#         """
#         # get the list of existing labels
#         existing_labels = self.labels
#         
#         # validate the input
#         if value.__class__ is not list:
#             raise ValueError("Input must be a list of two values: index and label")
#         
#         if len(value)!=2:
#             raise ValueError("Input must be a list of length 2")
#         
#         try:
#             index = int(value[0])
#         except ValueError:
#             raise ValueError("First item must be an integer kpoint index")
#         
#         # append 
#         label = str(value[1]) 
#         existing_labels.append([index,label])
#         
#         # sort
#         new_labels= sorted(existing_labels, key=lambda x:x[0])
#         
#         # overwrite the previous values
#         self.labels = new_labels
#      
#     def delete_label(self,index):
#         """
#         Delete the label at position 'index'. Works as the python command 
#         del list[index]
#         """
#         index = int(index)
#         existing_labels = self.get_labels()
#         del existing_labels[index]
#         self.set_labels(existing_labels)

    def set_cell_from_structure(self,structuredata):
        """
        Set a cell to be used for symmetry analysis from an AiiDA structure.
        Inherits both the cell and the pbc's.
        To set manually a cell, use "set_cell"
        
        :param structuredata: an instance of StructureData
        """
        from aiida.orm.data.structure import StructureData
        if not isinstance(structuredata,StructureData):
            raise ValueError("An instance of StructureData should be passed to "
                             "the KpointsData, found instead {}"
                             .format(structuredata.__class__))
        cell = structuredata.cell
        self.set_cell(cell,structuredata.pbc)
    
    def set_cell(self,cell,pbc=None):
        """
        Set a cell to be used for symmetry analysis.
        To set a cell from an AiiDA structure, use "set_cell_from_structure".
        
        :param cell: 3x3 matrix of cell vectors. Orientation: each row 
                     represent a lattice vector
        :param pbc: list of 3 booleans, True if in the nth crystal direction the
                    structure is periodic. Default = [True,True,True]
        """
        self.cell = cell
        if pbc is None:
            pbc = [True,True,True]
        self.pbc = pbc 
        self._load_cell_properties()
        
    def _load_cell_properties(self):
        """
        A function executed by the __init__ or by set_cell.
        If a cell is set, properties like a1,a2,a3,cosalpha,reciprocal_cell are 
        set as well, although they are not stored in the DB.
        """
        # save a lot of variables that are used later, and just depend on the
        # cell
        the_cell = numpy.array(self.cell)
        reciprocal_cell = 2.*numpy.pi*numpy.linalg.inv(the_cell)
        self.reciprocal_cell = reciprocal_cell
        self._a1 = numpy.array(the_cell[0,:])
        self._a2 = numpy.array(the_cell[1,:])
        self._a3 = numpy.array(the_cell[2,:])
        self._a = numpy.linalg.norm(self._a1)
        self._b = numpy.linalg.norm(self._a2)
        self._c = numpy.linalg.norm(self._a3)
        self._b1 = reciprocal_cell[0,:]
        self._b2 = reciprocal_cell[1,:]
        self._b3 = reciprocal_cell[2,:]
        self._cosalpha = numpy.dot(self._a2,self._a3)/self._b/self._c
        self._cosbeta  = numpy.dot(self._a3,self._a1)/self._c/self._a
        self._cosgamma = numpy.dot(self._a1,self._a2)/self._a/self._b
        # Note: a,b,c,alpha,beta and gamma are referred to the input cell
        # not to the 'conventional' or rotated cell.

    def set_kpoints_mesh(self,mesh,offset=[0.,0.,0.]):
        """
        Set KpointsData to represent a uniformily spaced mesh of kpoints in the
        Brillouin zone. This excludes the possibility of set/get kpoints
        
        :param mesh: a list of three integers, representing the size of the 
                 kpoint mesh along b1,b2,b3.
        :param (optional) offset: a list of three floats between 0 and 1.
                [0.,0.,0.] is Gamma centered mesh
                [0.5,0.5,0.5] is half shifted
                [1.,1.,1.] by periodicity should be equivalent to [0.,0.,0.]
                Default = [0.,0.,0.].
        """
        from aiida.common.exceptions import ModificationNotAllowed
        # validate
        try:
            the_mesh = tuple(int(i) for i in mesh)
            if len(the_mesh) != 3:
                raise ValueError
        except (IndexError,ValueError,TypeError):
            raise ValueError("The kpoint mesh must be a list of three integers")
        try:
            the_offset = tuple(float(i) for i in offset)
            if len(the_offset) != 3:
                raise ValueError
        except (IndexError,ValueError,TypeError):
            raise ValueError("The offset must be a list of three integers")
        # check that there is no list of kpoints saved already
        # I cannot have both of them at the same time
        try:
            _ = self.get_array('kpoints')
            raise ModificationNotAllowed("KpointsData has already a kpoint-"
                                         "list stored")
        except KeyError:
            pass
        
        # store
        self.set_attr('mesh',the_mesh)
        self.set_attr('offset',the_offset)

    def get_kpoints_mesh(self):
        """
        Get the mesh of kpoints.
        
        :raise AttributeError: if no mesh has been set
        :return mesh,offset: a list of 3 integers and a list of three 
                floats 0<x<1, representing the mesh and the offset of kpoints
        """
        mesh = self.get_attr('mesh')
        offset = self.get_attr('offset')
        return mesh, offset

    def _validate_kpoints_weights(self,kpoints,weights):
        """
        Validate the list of kpoints and of weights before storage.
        Kpoints and weights must be convertible to an array of Nx3 and N floats
        """
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
            if weights.shape[0] != kpoints.shape[0]:
                raise ValueError("Found {} weights but {} kpoints"
                                 .format(weights.shape[0], kpoints.shape[0]))
            if weights.dtype != numpy.dtype(numpy.float):
                raise ValueError("weights must be an array of type floats. "
                                 "Found instead {}".format(weights.dtype))
        
        return kpoints,weights

    def set_kpoints(self,kpoints,cartesian=False,labels=None,weights=None):
        """
        Set the list of kpoints. If a mesh has already been stored, raise a 
        ModificationNotAllowed
        
        :param kpoints: a list of kpoints, each kpoint being a list of three 
               coordinates (e.g. [[0.,0.,0.],[0.1,0.1,0.1],...])
        :param cartesian: if True, the coordinates given in input are treated 
                 as in cartesian units. If False, the coordinates are crystal,
                 i.e. in units of b1,b2,b3. Default = False
        :param labels: optional, the list of labels to be set for some of the 
                       kpoints. See labels for more info
        :param weights: optional, a list of floats with the weight associated
                        to the kpoint list 
        """
        from aiida.common.exceptions import ModificationNotAllowed
        # check that it is a 'dim'x #kpoints dimensional array
        the_kpoints,the_weights = self._validate_kpoints_weights(kpoints,weights)

        # change reference and always store in crystal coords
        if cartesian:
            the_kpoints = self._change_reference(the_kpoints,to_cartesian=False)
        
        # check that we did not saved a mesh already
        if self.get_attr('mesh',None) is not None:
            raise ModificationNotAllowed("KpointsData has already a mesh stored")
        
        # store
        self.set_array('kpoints',the_kpoints)
        if the_weights is not None:
            self.set_array('weights',the_weights)
        if labels is not None:
            self.labels = labels
   
    def get_kpoints(self,also_weights=False,cartesian=False):
        """
        Return the list of kpoints
        
        :param also_weights: if True, returns also the list of weights. 
            Default = False
        :param cartesian: if True, returns points in cartesian coordinates,
            otherwise, returns in crystal coordinates. Default = False.
        """
        try:
            kpoints = numpy.array(self.get_array('kpoints'))
        except KeyError:
            raise AttributeError("Before the get, first set a list of kpoints")
            
        try:
            if not all(self.pbc):
                for i in range(3):
                    if not self.pbc[i]:
                        kpoints[:,i] = 0.
        except AttributeError:
            # no pbc data found -> assume (True,True,True)
            pass;
        # note that this operation may lead to duplicates if the kpoints were
        # set thinking that everything is 3D.
        # Atm, it's up to the user to avoid duplication, if he cares.
        # in the future, add the bravais_lattice for 2d and 1d cases, 
        # and do a set() on the kpoints lists (before storing)
        
        if cartesian:
            kpoints = self._change_reference(kpoints,to_cartesian=True)
        
        if also_weights:
            try:
                the_weights = self.get_array('weights')
            except KeyError:
                raise AttributeError('No weights were set')
            
            weights = numpy.array(the_weights)
            return kpoints,weights
        else:
            return kpoints
         
    def _change_reference(self,kpoints,to_cartesian=True):
        """
        Change reference system, from cartesian to crystal coordinates (units 
        of b1,b2,b3) or viceversa.
        :param kpoints: a list of (3) point coordinates
        :return kpoints: a list of (3) point coordinates in the new reference
        """
        if not isinstance(kpoints,numpy.ndarray):
            raise ValueError("kpoints must be a numpy.array for method"
                             "_change_reference()")
        
        try:
            rec_cell = self.reciprocal_cell
        except AttributeError:
            rec_cell = numpy.eye(3)
            # raise InputError("Cannot change coords without cell")
        #trec_cell = numpy.transpose( numpy.array(rec_cell) )
        if to_cartesian:
            matrix = rec_cell
        else:
            matrix = numpy.linalg.inv(rec_cell)
        
        # note: kpoints is a list Nx3, matrix is 3x3.
        # hence, first transpose kpoints, then multiply, finally transpose it back
        return numpy.transpose(numpy.dot(matrix,numpy.transpose(kpoints)))
    
    def set_kpoints_path(self,value=None,tot_num_kpoints=None,
                           cartesian=False):
        """
        Set a path of kpoints in the Brillouin zone.
        
        :param value: description of the path, in various possible formats.
            * None: automatically sets all irreducible high symmetry paths. 
                    Requires that a cell was set
            *
        [('G','M'), (...), ...]
        [('G','M',30), (...), ...]
        [('G',(0,0,0),'M',(1,1,1)), (...), ...]
        [('G',(0,0,0),'M',(1,1,1),30), (...), ...]       
        optional: tot_num_kpoints. can be set if value is None or a list of couplets
        """
        def _is_path_1(path):
            try:
                are_two = all( [ len(i)==2 for i in path ] )
                if not are_two:
                    return False

                for i in path:
                    are_str = all( [ isinstance(b,str) for b in i ] )
                    if not are_str:
                        return False
            except IndexError:
                return False
            return True

        def _is_path_2(path):
            try:
                are_three = all( [ len(i)==3 for i in path ] )
                if not are_three:
                    return False

                are_good = all( [ all([isinstance(b[0],str),
                                       isinstance(b[1],str),
                                       isinstance(b[2],int)])
                                  for b in path ] )
                if not are_good:
                    return False
            except IndexError:
                return False
            return True
        
        def _is_path_3(path):
            #[('G',(0,0,0),'M',(1,1,1)), (...), ...]
            try:
                _ = len(path)
                are_four = all([len(i)==4 for i in path])
                if not are_four:
                    return False
                have_labels = all( all([isinstance(i[0],str),isinstance(i[2],str)]) for i in path )
                if not have_labels:
                    return False
                for i in path:
                    coord1 = [float(j) for j in i[1]]
                    coord2 = [float(j) for j in i[3]]
                    if len(coord1)!=3 or len(coord2)!=3:
                        return False
            except (TypeError,IndexError):
                return False
            return True

        def _is_path_4(path):
            #[('G',(0,0,0),'M',(1,1,1),30), (...), ...]
            try:
                _ = len(path)
                are_five = all([len(i)==5 for i in path])
                if not are_five:
                    return False
                have_labels = all( all([isinstance(i[0],str),isinstance(i[2],str)]) for i in path )
                if not have_labels:
                    return False
                have_points_num = all([ isinstance(i[4],int) for i in path ]) 
                if not have_points_num:
                    return False
                for i in path:
                    coord1 = [float(j) for j in i[1]]
                    coord2 = [float(j) for j in i[3]]
                    if len(coord1)!=3 or len(coord2)!=3:
                        return False
            except (TypeError,IndexError):
                return False
            return True
        
        def _num_points_from_coordinates(path,point_coordinates,
                                             tot_num_kpoints=None):
            # NOTE: this way of creating intervals ensures equispaced objects 
            #       in crystal coordinates of b1,b2,b3
            distances = [ numpy.linalg.norm(numpy.array(point_coordinates[i[0]]) -
                                            numpy.array(point_coordinates[i[1]])
                                            ) for i in path ]
            # Use max_points_per_interval as the default guess for automatically
            # guessing the number of points
            max_point_per_interval = 10
            max_interval = max(distances)
            points_per_piece = [ int(max_point_per_interval*i/max_interval) for i in distances ]
            
            # if tot_num_kpoints is inputted, scale the number of points
            if tot_num_kpoints is not None:
                # first scale
                tot = sum(points_per_piece)
                points = [ int(float(i)/tot*tot_num_kpoints) for i in points_per_piece ]
                # there might still some leftovers due to roundoff:
                # add some more points in the first segments
                i=0
                while sum(points)<tot_num_kpoints:
                    points[i] += 1
                    i+=1
                return points
            else:
                return points_per_piece
        
        if cartesian:
            try:
                _ = self.cell
            except AttributeError:
                raise ValueError("To use cartesian coordinates, a cell must "
                                 "be provided")

        if value is None:
            try:
                _ = self.cell
            except AttributeError:
                raise ValueError("Cannot set a path not even knowing the "
                                 "kpoints or at least the cell")
            point_coordinates,path = self.get_special_points()
            num_points = _num_points_from_coordinates(path,point_coordinates,
                                                      tot_num_kpoints)

        elif _is_path_1(value):
            # in the form [('X','M'),(...),...]
            try:
                _ = self.cell
            except AttributeError:
                raise ValueError("Cannot set a path not even knowing the "
                                 "kpoints or at least the cell")

            path = value
            point_coordinates,_ = self.get_special_points()
            num_points = _num_points_from_coordinates(path,point_coordinates,
                                                      tot_num_kpoints)
            
        elif _is_path_2(value):
            # [('G','M',30), (...), ...]
            try:
                _ = self.cell
            except AttributeError:
                raise ValueError("Cannot set a path not even knowing the "
                                 "kpoints or at least the cell")

            path = [ (i[0],i[1]) for i in value ]
            point_coordinates,_ = self.get_special_points()
            num_points = [i[2] for i in value]

        elif _is_path_3(value):
            #[('G',(0,0,0),'M',(1,1,1)), (...), ...]
            path = [ ( i[0],i[2] ) for i in value ]
            
            point_coordinates = {}
            for piece in value:
                if piece[0] in point_coordinates:
                    if point_coordinates[piece[0]] != piece[1]: 
                        raise ValueError("Different points cannot have the same label")
                else: 
                    if cartesian:
                        point_coordinates[piece[0]] = self._change_reference(numpy.array([piece[1]]),
                                                                             to_cartesian=False)[0]
                    else:
                        point_coordinates[piece[0]] = piece[1]
                if piece[2] in point_coordinates:
                    if point_coordinates[piece[2]] != piece[3]: 
                        raise ValueError("Different points cannot have the same label")
                else: 
                    if cartesian:
                        point_coordinates[piece[2]] = self._change_reference(numpy.array([piece[3]]),
                                                                             to_cartesian=False)[0]
                    else:
                        point_coordinates[piece[2]] = piece[3]

            num_points = _num_points_from_coordinates(path,point_coordinates,
                                                      tot_num_kpoints)
            
        elif _is_path_4(value):
            #[('G',(0,0,0),'M',(1,1,1),30), (...), ...]
            path = [ ( i[0],i[2] ) for i in value ]

            point_coordinates = {}
            for piece in value:
                if piece[0] in point_coordinates:
                    if point_coordinates[piece[0]] != piece[1]: 
                        raise ValueError("Different points cannot have the same label")
                else: 
                    if cartesian:
                        point_coordinates[piece[0]] = self._change_reference(numpy.array([piece[1]]),
                                                                             to_cartesian=False)[0]
                    else:
                        point_coordinates[piece[0]] = piece[1]
                if piece[2] in point_coordinates:
                    if point_coordinates[piece[2]] != piece[3]: 
                        raise ValueError("Different points cannot have the same label")
                else:
                    if cartesian:
                        point_coordinates[piece[2]] = self._change_reference(numpy.array([piece[3]]),
                                                                             to_cartesian=False)[0]
                    else:
                        point_coordinates[piece[2]] = piece[3]
                    
            num_points = [ i[4] for i in value ]
            
        else:
            raise ValueError("Input format not recognized")
        
        kpoints = [ tuple(point_coordinates[path[0][0]]) ]
        labels = [ (0,path[0][0]) ]
        
        for count_piece,i in enumerate(path):
            ini_label = i[0]
            end_label = i[1]
            ini_coord = point_coordinates[ini_label]
            end_coord = point_coordinates[end_label]
            
            path_piece = zip(numpy.linspace(ini_coord[0],end_coord[0],
                                            num_points[count_piece]),
                             numpy.linspace(ini_coord[1],end_coord[1],
                                            num_points[count_piece]),
                             numpy.linspace(ini_coord[2],end_coord[2],
                                            num_points[count_piece]),
                             )
            
            for count,j in enumerate(path_piece):
                if all(numpy.array(kpoints[-1]) == j):
                    continue # avoid duplcates
                else:
                    kpoints.append(j)
                   
                # add labels for the first and last point
                if count==0:
                    labels.append( (len(kpoints)-1,ini_label) )
                if count==len(path_piece)-1:
                    labels.append( (len(kpoints)-1,end_label) )
                    
        # I still have some duplicates in the labels: eliminate them
        sorted(set(labels), key=lambda x: x[0] )
        
        self.set_kpoints(kpoints)
        self.labels = labels            
        
    def _find_bravais_info(self,epsilon_length=_default_epsilon_length,
                           epsilon_angle=_default_epsilon_angle):
        """
        Finds the Bravais lattice of the cell passed in input to the Kpoint class

        :return: a dictionary, with keys short_name, expanded_name, number
        """
        # load vectors
        a1 = self._a1
        a2 = self._a2
        a3 = self._a3
        a = self._a
        b = self._b
        c = self._c
        cosa = self._cosalpha
        cosb = self._cosbeta
        cosc = self._cosgamma
        
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
                    
            # if it doesn't fall in the above, is triclinic
            else:
                bravais_info = {"short_name":"tri",
                                "extended_name":"triclinic",
                                "index":14,
                                }
                # the check for triclinic variations is at the end of the method
                


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
            
            # if it doesn't fall in the above, is triclinic
            else:
                bravais_info = {"short_name":"tri",
                                "extended_name":"triclinic",
                                "index":14,
                                }
                # the check for triclinic variations is at the end of the method



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

    def find_bravais_lattice(self,epsilon_length=_default_epsilon_length,
                                  epsilon_angle=_default_epsilon_angle):
        """
        Analyze the symmetry of the cell. Allows to relax or tighten the 
        thresholds used to compare angles and lengths of the cell. Save the 
        information of the cell used for later use (like getting special 
        points). It has to be used if the user wants to be sure the right 
        symmetries are recognized. Otherwise, this function is automatically 
        called with the default values.
        
        If the right symmetry is not found, be sure also you are providing cells
        with enough digits.
        
        If node is already stored, just returns the symmetry found before 
        storing (if any).
        
        :return (str) lattice_name: the name of the bravais lattice and its 
             eventual variation  
        """
        if self._to_be_stored:
            bravais_lattice = self._find_bravais_info(epsilon_angle=epsilon_angle,
                                                   epsilon_length=epsilon_length)
            self.bravais_lattice = bravais_lattice
        else:
            bravais_info = self.bravais_lattice
        
        try:
            variation = ", variation: {}".format( bravais_info['variation'] )
        except KeyError:
            variation = ""
        
        return bravais_info['extended_name'] + variation
    
    def get_special_points(self,cartesian=False):
        """
        Get the special point and path of a given structure.
        Coordinates are based on the paper: 
            arXiv:1004.2974, W. Setyawan, S. Curtarolo
        :param cartesian: If true, returns points in cartesian coordinates.
                           Crystal coordinates otherwise. Default=False 
        :return special_points,path: special_points: a dictionary of 
                point_name:point_coords key,values.
                path: the suggested path which goes through all high symmetry 
                      lines. A list of lists for all path segments.
                      e.g. [('G','X'),('X','M'),...]
                      It's not necessarily a continous line.
        """
        # recognize which bravais lattice we are dealing with
        bravais_info = self._get_or_create_bravais_lattice()
        
        # pick the information about the special k-points
        # simple cubic
        if bravais_info['index']==1:
            special_points =  {'G':[0., 0., 0. ],
                               'M':[0.5,0.5,0. ],
                               'R':[0.5,0.5,0.5],
                               'X':[0., 0.5,0. ],
                               }
            path = [('G','X'),
                    ('X','M'),
                    ('M','G'),
                    ('G','R'),
                    ('R','X'),
                    ('M','R'),
                    ]
                    
        # face centered cubic
        elif bravais_info['index']==2:
            special_points =  {'G':[0.,   0.,   0.   ],
                               'K':[3./8.,3./8.,0.75 ],
                               'L':[0.5,  0.5,  0.5  ],
                               'U':[5./8.,0.25, 5./8.],
                               'W':[0.5,  0.25, 0.75 ],
                               'X':[0.5,  0.,   0.5  ],
                              }
            path = [('G','X'),
                    ('X','W'),
                    ('W','K'),
                    ('K','G'),
                    ('G','L'),
                    ('L','U'),
                    ('U','W'),
                    ('W','L'),
                    ('L','K'),
                    ('U','X'),
                    ]

        # body centered cubic
        elif bravais_info['index']==3:
            special_points = {'G':[0.,  0.,  0.  ],
                              'H':[0.5,-0.5, 0.5 ],
                              'P':[0.25,0.25,0.25],
                              'N':[0.,  0.,  0.5 ],
                              }
            path = [('G','H'),
                    ('H','N'),
                    ('N','G'),
                    ('G','P'),
                    ('P','H'),
                    ('P','N'),
                    ]

        # Tetragonal
        elif bravais_info['index'] == 4:
            special_points = {'G':[0., 0., 0.  ],
                              'A':[0.5,0.5,0.5 ],
                              'M':[0.5,0.5,0.  ],
                              'R':[0., 0.5,0.5 ],
                              'X':[0., 0.5,0.  ],
                              'Z':[0., 0., 0.5 ],
                              }
            path = [('G','X'),
                    ('X','M'),
                    ('M','G'),
                    ('G','Z'),
                    ('Z','R'),
                    ('R','A'),
                    ('A','Z'),
                    ('X','R'),
                    ('M','A'),
                    ]
                        
        # body centered tetragonal
        elif bravais_info['index']==5:
            if bravais_info['variation']=='bct1':
                # Body centered tetragonal bct1
                eta = bravais_info['extra']['eta']
                special_points = {'G':[0.,  0.,    0.   ],
                                  'M':[-0.5,0.5,   0.5  ],
                                  'N':[0.,  0.5,   0.   ],
                                  'P':[0.25,0.25,  0.25 ],
                                  'X':[0.,  0.,    0.5  ],
                                  'Z':[eta, eta,  -eta  ],
                                  'Z1':[-eta,1.-eta,eta  ],
                                  }
                path = [('G','X'),
                        ('X','M'),
                        ('M','G'),
                        ('G','Z'),
                        ('Z','P'),
                        ('P','N'),
                        ('N','Z1'),
                        ('Z1','M'),
                        ('X','P'),
                        ]

            else: # bct2
                # Body centered tetragonal bct2
                eta = bravais_info['extra']['eta']
                csi = bravais_info['extra']['csi']
                special_points = {
                        'G':[0.,  0.,   0.   ],
                        'N':[0.,  0.5,  0.   ],
                        'P':[0.25,0.25, 0.25 ],
                        'S':[-eta,eta,  eta  ],
                        'S1':[eta, 1-eta,-eta],
                        'X':[0.,  0.,   0.5  ],
                        'Y':[-csi,csi,  0.5  ],
                        'Y1':[0.5, 0.5, -csi ],
                        'Z':[0.5, 0.5, -0.5  ],
                        }
                path = [('G' ,'X' ),
                        ('X' ,'Y' ),
                        ('Y' ,'S' ),
                        ('S' ,'G' ),
                        ('G' ,'Z' ),
                        ('Z' ,'S1'),
                        ('S1','N' ),
                        ('N' ,'P' ),
                        ('P' ,'Y1'),
                        ('Y1','Z' ),
                        ('X' ,'P' ),
                        ]

        # orthorhombic
        elif bravais_info['index'] == 6:
            special_points = {'G':[0.,  0.,  0.  ],
                              'R':[0.5, 0.5, 0.5 ],
                              'S':[0.5, 0.5, 0.  ],
                              'T':[0.,  0.5, 0.5 ],
                              'U':[0.5, 0.,  0.5 ],
                              'X':[0.5, 0.,  0.  ],
                              'Y':[0.,  0.5, 0.  ],
                              'Z':[0.,  0.,  0.5 ],
                              }
            path = [('G','X' ),
                    ('X','S' ),
                    ('S','Y' ),
                    ('Y','G' ),
                    ('G','Z' ),
                    ('Z','U' ),
                    ('U','R' ),
                    ('R','T' ),
                    ('T','Z' ),
                    ('Y','T' ),
                    ('U','X' ),
                    ('S','R' ),
                    ]

        # face-centered orthorhombic
        elif bravais_info['index'] == 7:
            if bravais_info['variation']=='orcf1':
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                special_points = {'G' :[0.,  0.,      0.  ],
                                  'A' :[0.5, 0.5+csi, csi ],
                                  'A1':[0.5,0.5-csi,1.-csi],
                                  'L' :[0.5, 0.5,     0.5 ],
                                  'T' :[1.,  0.5,     0.5 ],
                                  'X' :[0.,  eta,     eta ],
                                  'X1':[1., 1.-eta,1.-eta ],
                                  'Y' :[0.5, 0.,      0.5 ],
                                  'Z' :[0.5, 0.5,     0.  ],
                                  }
                path = [('G' ,'Y' ),
                        ('Y' ,'T' ),
                        ('T' ,'Z' ),
                        ('Z' ,'G' ),
                        ('G' ,'X' ),
                        ('X' ,'A1'),
                        ('A1','Y' ),
                        ('T' ,'X1'),
                        ('X' ,'A' ),
                        ('A' ,'Z' ),
                        ('L' ,'G' ),
                        ]

            elif bravais_info['variation']=='orcf2':
                eta = bravais_info['extra']['eta']
                dlt = bravais_info['extra']['dlt']
                phi = bravais_info['extra']['phi']
                special_points = {'G' :[0.,  0.,      0.  ],
                                  'C' :[0.5,0.5-eta,1.-eta],
                                  'C1':[0.5,0.5+eta, eta  ],
                                  'D' :[0.5-dlt,0.5,1.-dlt],
                                  'D1':[0.5+dlt,0.5, dlt  ],
                                  'L' :[0.5, 0.5,    0.5  ],
                                  'H' :[1.-phi,0.5-phi,0.5],
                                  'H1':[phi,0.5+phi, 0.5  ],
                                  'X' :[0.,  0.5,    0.5  ],
                                  'Y' :[0.5, 0.,     0.5  ],
                                  'Z' :[0.5, 0.5,    0.   ],
                                  }
                path = [('G' ,'Y' ),
                        ('Y' ,'C' ),
                        ('C' ,'D' ),
                        ('D' ,'X' ),
                        ('X' ,'G' ),
                        ('G' ,'Z' ),
                        ('Z' ,'D1'),
                        ('D1','H' ),
                        ('H' ,'C' ),
                        ('C1','Z' ),
                        ('X' ,'H1'),
                        ('H' ,'Y' ),
                        ('L' ,'G' ),
                        ]

            else:
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                special_points = {'G' :[0.,  0.,      0.  ],
                                  'A' :[0.5, 0.5+csi, csi ],
                                  'A1':[0.5,0.5-csi,1.-csi],
                                  'L' :[0.5, 0.5,     0.5 ],
                                  'T' :[1.,  0.5,     0.5 ],
                                  'X' :[0.,  eta,     eta ],
                                  'X1':[1., 1.-eta,1.-eta ],
                                  'Y' :[0.5, 0.,      0.5 ],
                                  'Z' :[0.5, 0.5,     0.  ],
                                  }
                path = [('G' ,'Y' ),
                        ('Y' ,'T' ),
                        ('T' ,'Z' ),
                        ('Z' ,'G' ),
                        ('G' ,'X' ),
                        ('X' ,'A1'),
                        ('A1','Y' ),
                        ('X' ,'A' ),
                        ('A' ,'Z' ),                        
                        ('L' ,'G' ),
                        ]

        # Body centered orthorhombic
        elif bravais_info['index']==8:
            csi = bravais_info['extra']['csi']
            dlt = bravais_info['extra']['dlt']
            eta = bravais_info['extra']['eta']
            mu  = bravais_info['extra']['mu']
            special_points = {'G' :[0.,   0.,   0.   ],
                              'L' :[-mu,  mu, 0.5-dlt],
                              'L1':[mu,  -mu, 0.5+dlt],
                              'L2':[0.5-dlt,0.5+dlt,-mu],
                              'R' :[0.,  0.5,   0.   ],
                              'S' :[0.5,  0.,   0.   ],
                              'T' :[0.,   0.,   0.5  ],
                              'W' :[0.25,0.25,  0.25 ],
                              'X' :[-csi, csi,  csi  ],
                              'X1':[csi,1.-csi,-csi  ],
                              'Y' :[eta, -eta,  eta  ],
                              'Y1':[1.-eta, eta,-eta ],
                              'Z' :[0.5,  0.5,  -0.5 ],
                              }
            path = [('G' ,'X' ),
                    ('X' ,'L' ),
                    ('L' ,'T' ),
                    ('T' ,'W' ),
                    ('W' ,'R' ),
                    ('R' ,'X1'),
                    ('X1','Z' ),
                    ('Z' ,'G' ),
                    ('G' ,'Y' ),                        
                    ('Y' ,'S' ),
                    ('S' ,'W' ),
                    ('L1','Y' ),
                    ('Y1','Z' ),
                    ]

        # C-centered orthorhombic
        elif bravais_info['index']==9:
            csi = bravais_info['extra']['csi']
            special_points = {'G' :[0.,  0.,     0.  ],
                              'A' :[csi, csi,    0.5 ],
                              'A1':[-csi,1.-csi, 0.5 ],
                              'R' :[0.,  0.5,    0.5 ],
                              'S' :[0.,  0.5,    0.  ],
                              'T' :[-0.5,0.5,    0.5 ],
                              'X' :[csi, csi,    0.  ],
                              'X1':[-csi,1.-csi, 0.  ],
                              'Y' :[-0.5,0.5,    0.  ],
                              'Z' :[0.,  0.,     0.5 ],
                              }
            path = [('G' ,'X' ),
                    ('X' ,'S' ),
                    ('S' ,'R' ),
                    ('R' ,'A' ),
                    ('A' ,'Z' ),
                    ('Z' ,'G' ),
                    ('G' ,'Y' ),
                    ('Y' ,'X1'),
                    ('X1','A1'),                        
                    ('A1','T' ),
                    ('T' ,'Y' ),
                    ('Z' ,'T' ),
                    ]

        # Hexagonal
        elif bravais_info['index']==10:
            special_points = {'G':[0.,   0.,   0. ],
                              'A':[0.,   0.,   0.5],
                              'H':[1./3.,1./3.,0.5],
                              'K':[1./3.,1./3.,0. ],
                              'L':[0.5,  0.,   0.5],
                              'M':[0.5,  0.,   0. ],
                              }
            path = [('G' ,'M' ),
                    ('M' ,'K' ),
                    ('K' ,'G' ),
                    ('G' ,'A' ),
                    ('A' ,'L' ),
                    ('L' ,'H' ),
                    ('H' ,'A' ),
                    ('L' ,'M' ),
                    ('K' ,'H' ),                        
                    ]

        # rhombohedral
        elif bravais_info['index']==11:
            if bravais_info['variation']=='rhl1':
                eta = bravais_info['extra']['eta']
                nu  = bravais_info['extra']['nu']
                special_points = {'G' :[0.,   0.,    0.  ],
                                  'B' :[eta, 0.5,1.-eta  ],
                                  'B1':[0.5,1.-eta,eta-1.],
                                  'F' :[0.5, 0.5,    0.  ],
                                  'L' :[0.5,  0.,    0.  ],
                                  'L1':[0. ,  0.,   -0.5 ],
                                  'P' :[eta,  nu,    nu  ],
                                  'P1':[1.-nu,1.-nu,1.-eta],
                                  'P2':[nu,   nu, eta-1. ],
                                  'Q' :[1.-nu,nu,    0.  ],
                                  'X' :[nu,   0.,   -nu  ],
                                  'Z' :[0.5,  0.5,   0.5 ],
                                  }
                path = [('G' ,'L' ),
                        ('L' ,'B1'),
                        ('B' ,'Z' ),
                        ('Z' ,'G' ),
                        ('G' ,'X' ),
                        ('Q' ,'F' ),
                        ('F' ,'P1'),
                        ('P1','Z' ),
                        ('L' ,'P' ),                        
                        ]

            else: # Rhombohedral rhl2
                eta = bravais_info['extra']['eta']
                nu  = bravais_info['extra']['nu']
                special_points = {'G' :[0.,     0.,   0.  ],
                                  'F' :[0.5,  -0.5,   0.  ],
                                  'L' :[0.5,    0.,   0.  ],
                                  'P' :[1.-nu,-nu,1. -nu  ],
                                  'P1':[nu,  nu-1.,  nu-1.],
                                  'Q' :[eta,   eta,   eta ],
                                  'Q1':[1.-eta,-eta, -eta ],
                                  'Z' :[0.5,  -0.5,   0.5],
                                  }
                path = [('G' ,'P' ),
                        ('P' ,'Z' ),
                        ('Z' ,'Q' ),
                        ('Q' ,'G' ),
                        ('G' ,'F' ),
                        ('F' ,'P1'),
                        ('P1','Q1'),
                        ('Q1','L' ),
                        ('L' ,'Z' ),
                        ]

        # monoclinic
        elif bravais_info['index']==12:
            eta = bravais_info['extra']['eta']
            nu = bravais_info['extra']['nu']
            special_points = {'G' :[ 0.,   0.,   0.  ],
                              'A' :[0.5,  0.5,   0.  ],
                              'C' :[ 0.,  0.5,   0.5 ],
                              'D' :[0.5,   0.,   0.5 ],
                              'D1':[0.5,   0.,  -0.5 ],
                              'E' :[0.5,  0.5,   0.5 ],
                              'H' :[ 0.,  eta, 1.-nu ],
                              'H1':[ 0.,1.-eta,  nu  ],
                              'H2':[ 0.,  eta,  -nu  ],
                              'M' :[0.5,  eta, 1.-nu ],
                              'M1':[0.5,1.-eta,  nu  ],
                              'M2':[0.5,  eta,  -nu  ],
                              'X' :[ 0.,  0.5,   0.  ],
                              'Y' :[ 0.,   0.,   0.5 ],
                              'Y1':[ 0.,   0.,  -0.5 ],
                              'Z' :[0.5,   0.,   0.  ],
                              }
            path = [('G' ,'Y' ),
                    ('Y' ,'H' ),
                    ('H' ,'C' ),
                    ('C' ,'E' ),
                    ('E' ,'M1'),
                    ('M1','A' ),
                    ('A' ,'X' ),
                    ('X' ,'H1'),
                    ('M' ,'D' ),                        
                    ('D' ,'Z' ),
                    ('Y' ,'D' ),
                    ]

        elif bravais_info['index'] == 13:
            if bravais_info['variation']=='mclc1':
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                psi = bravais_info['extra']['psi']
                phi = bravais_info['extra']['phi']
                special_points = {'G' :[ 0.,   0.,   0.  ],
                                  'N' :[0.5,   0.,   0.  ],
                                  'N1':[ 0., -0.5,   0.  ],
                                  'F' :[1.-csi,1.-csi,1.-eta],
                                  'F1':[  csi,  csi,   eta],
                                  'F2':[  csi, -csi,1.-eta],
                                  'F3':[1.-csi,-csi,1.-eta],
                                  'I' :[  phi, 1.-phi, 0.5],
                                  'I1':[1.-phi, phi-1.,0.5],
                                  'L' :[ 0.5,    0.5,  0.5],
                                  'M' :[ 0.5,     0.,  0.5],
                                  'X' :[1.-psi,psi-1., 0. ],
                                  'X1':[psi,  1.-psi,  0. ],
                                  'X2':[psi-1., -psi,  0. ],
                                  'Y' :[ 0.5,    0.5,  0. ],
                                  'Y1':[-0.5,   -0.5,  0. ],
                                  'Z' :[0.,       0.,  0.5],
                                  }
                path = [('G' ,'Y' ),
                        ('Y' ,'F' ),
                        ('F' ,'L' ),
                        ('L' ,'I' ),
                        ('I1','Z' ),
                        ('Z' ,'F1'),
                        ('Y' ,'X1'),
                        ('X' ,'G' ),
                        ('G' ,'N' ),                                                
                        ('M' ,'G' ),
                        ]

            elif bravais_info['variation']=='mclc2':
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                psi = bravais_info['extra']['psi']
                phi = bravais_info['extra']['phi']
                special_points = {'G' :[ 0.,   0.,   0.  ],
                                  'N' :[0.5,   0.,   0.  ],
                                  'N1':[ 0., -0.5,   0.  ],
                                  'F' :[1.-csi,1.-csi,1.-eta],
                                  'F1':[  csi,  csi,   eta],
                                  'F2':[  csi, -csi,1.-eta],
                                  'F3':[1.-csi,-csi,1.-eta],
                                  'I' :[  phi, 1.-phi, 0.5],
                                  'I1':[1.-phi, phi-1.,0.5],
                                  'L' :[ 0.5,    0.5,  0.5],
                                  'M' :[ 0.5,     0.,  0.5],
                                  'X' :[1.-psi,psi-1., 0. ],
                                  'X1':[psi,  1.-psi,  0. ],
                                  'X2':[psi-1., -psi,  0. ],
                                  'Y' :[ 0.5,    0.5,  0. ],
                                  'Y1':[-0.5,   -0.5,  0. ],
                                  'Z' :[0.,       0.,  0.5],
                                  }
                path = [('G' ,'Y' ),
                        ('Y' ,'F' ),
                        ('F' ,'L' ),
                        ('L' ,'I' ),
                        ('I1','Z' ),
                        ('Z' ,'F1'),                        
                        ('N' ,'G' ),
                        ('G' ,'M' ),
                        ]

            elif bravais_info['variation']=='mclc3':
                mu  = bravais_info['extra']['mu']
                dlt = bravais_info['extra']['dlt']
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                phi = bravais_info['extra']['phi']
                psi = bravais_info['extra']['psi']
                special_points = {
                              'G' :[  0.,   0.,  0.   ],
                              'F' :[1.-phi,1-phi,1.-psi],
                              'F1':[ phi,phi-1., psi  ],
                              'F2':[1.-phi,-phi,1.-psi],
                              'H' :[ csi,  csi,  eta  ],
                              'H1':[1.-csi,-csi,1.-eta],
                              'H2':[-csi, -csi, 1.-eta],
                              'I' :[ 0.5, -0.5,  0.5  ],
                              'M' :[ 0.5,   0.,  0.5  ],
                              'N' :[ 0.5,   0.,  0.   ],
                              'N1':[ 0. , -0.5,  0.   ],
                              'X' :[ 0.5, -0.5,  0.   ],
                              'Y' :[ mu ,   mu,  dlt  ],
                              'Y1':[1.-mu, -mu, -dlt  ],
                              'Y2':[-mu ,  -mu, -dlt  ],
                              'Y3':[ mu ,mu-1.,  dlt  ],
                              'Z' :[ 0. ,   0.,  0.5  ],
                              }
                path = [('G' ,'Y' ),
                        ('Y' ,'F' ),
                        ('F' ,'H' ),
                        ('H' ,'Z' ),
                        ('Z' ,'I' ),
                        ('I' ,'F1'),
                        ('H1','Y1'),
                        ('Y1','X' ),
                        ('X' ,'F' ),                        
                        ('G' ,'N' ),                        
                        ('M' ,'G' ),
                        ]

            elif bravais_info['variation']=='mclc4':
                mu  = bravais_info['extra']['mu']
                dlt = bravais_info['extra']['dlt']
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                phi = bravais_info['extra']['phi']
                psi = bravais_info['extra']['psi']
                special_points = {'G' :[  0.,   0.,  0.   ],
                                  'F' :[1.-phi,1-phi,1.-psi],
                                  'F1':[ phi,phi-1., psi  ],
                                  'F2':[1.-phi,-phi,1.-psi],
                                  'H' :[ csi,  csi,  eta  ],
                                  'H1':[1.-csi,-csi,1.-eta],
                                  'H2':[-csi, -csi, 1.-eta],
                                  'I' :[ 0.5, -0.5,  0.5  ],
                                  'M' :[ 0.5,   0.,  0.5  ],
                                  'N' :[ 0.5,   0.,  0.   ],
                                  'N1':[ 0. , -0.5,  0.   ],
                                  'X' :[ 0.5, -0.5,  0.   ],
                                  'Y' :[ mu ,   mu,  dlt  ],
                                  'Y1':[1.-mu, -mu, -dlt  ],
                                  'Y2':[-mu ,  -mu, -dlt  ],
                                  'Y3':[ mu ,mu-1.,  dlt  ],
                                  'Z' :[ 0. ,   0.,  0.5  ],
                                  }
                path = [('G' ,'Y' ),
                        ('Y' ,'F' ),
                        ('F' ,'H' ),
                        ('H' ,'Z' ),
                        ('Z' ,'I' ),                        
                        ('H1','Y1'),
                        ('Y1','X' ),
                        ('X' ,'G' ),
                        ('G' ,'N' ),                        
                        ('M' ,'G' ),
                        ]

            else:
                csi = bravais_info['extra']['csi']
                mu  = bravais_info['extra']['mu']
                omg = bravais_info['extra']['omg']
                eta = bravais_info['extra']['eta']
                nu  = bravais_info['extra']['nu']
                dlt = bravais_info['extra']['dlt']
                rho = bravais_info['extra']['rho']
                special_points = {
                              'G' :[  0.,   0.,  0.   ],
                              'F' :[  nu,   nu,  omg  ],
                              'F1':[1.-nu,1.-nu,1.-omg],
                              'F2':[  nu, nu-1., omg  ],
                              'H' :[ csi,  csi,  eta  ],
                              'H1':[1.-csi,-csi,1.-eta],
                              'H2':[-csi, -csi, 1.-eta],
                              'I' :[rho,1.-rho,  0.5  ],
                              'I1':[1.-rho,rho-1.,0.5],
                              'L' :[ 0.5,  0.5,  0.5  ],
                              'M' :[ 0.5,  0.,   0.5],
                              'N' :[ 0.5,  0.,   0.   ],
                              'N1':[ 0.,  -0.5,  0.   ],
                              'X' :[ 0.5, -0.5,  0.   ],
                              'Y' :[ mu ,   mu,  dlt  ],
                              'Y1':[1.-mu, -mu, -dlt  ],
                              'Y2':[-mu ,  -mu, -dlt  ],
                              'Y3':[ mu ,mu-1.,  dlt  ],
                              'Z' :[ 0. ,   0.,  0.5  ],
                              }
                path = [('G' ,'Y' ),
                        ('Y' ,'F' ),
                        ('F' ,'L' ),
                        ('L' ,'I' ),
                        ('I1','Z' ),
                        ('Z' ,'H' ),
                        ('H' ,'F1'),
                        ('H1','Y1'),
                        ('Y1','X' ),                        
                        ('X' ,'G' ),
                        ('G' ,'N' ),
                        ('M' ,'G' ),
                        ]

        if bravais_info['index']==14:
            if bravais_info['variation']=='tri1a' or bravais_info['variation']=='tri2a':
                special_points = {'G':[ 0.0, 0.0, 0.0 ],
                                  'L':[ 0.5, 0.5, 0.0 ],
                                  'M':[ 0.0, 0.5, 0.5 ],
                                  'N':[ 0.5, 0.0, 0.5 ],
                                  'R':[ 0.5, 0.5, 0.5 ],
                                  'X':[ 0.5, 0.0, 0.0 ],
                                  'Y':[ 0.0, 0.5, 0.0 ],
                                  'Z':[ 0.0, 0.0, 0.5 ],
                                  }
                path = [('X' ,'G' ),
                        ('G' ,'Y' ),
                        ('L' ,'G' ),
                        ('G' ,'Z' ),
                        ('N' ,'G' ),
                        ('G' ,'M' ),                        
                        ('R' ,'G' ),
                        ]

            else:
                special_points = {'G':[ 0.0, 0.0, 0.0 ],
                                  'L':[ 0.5,-0.5, 0.0 ],
                                  'M':[ 0.0, 0.0, 0.5 ],
                                  'N':[-0.5,-0.5, 0.5 ],
                                  'R':[ 0.0,-0.5, 0.5 ],
                                  'X':[ 0.0,-0.5, 0.0 ],
                                  'Y':[ 0.5, 0.0, 0.0 ],
                                  'Z':[-0.5, 0.0, 0.5 ],
                                  }
                path = [('X' ,'G' ),
                        ('G' ,'Y' ),
                        ('L' ,'G' ),
                        ('G' ,'Z' ),                        
                        ('N' ,'G' ),
                        ('G' ,'M'),
                        ('R' ,'G' ),
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

        the_special_points = {}
        for k in special_points.iterkeys():
            the_special_points[k] = permute(special_points[k],permutation)
            
        # output crystal or cartesian
        if cartesian:
            the_abs_special_points = {}
            for k in the_special_points.iterkeys():
                the_abs_special_points[k] = self._change_reference(the_special_points[k],
                                                                   to_cartesian=True)
    
            return the_abs_special_points,path
        else:
            return the_special_points,path






