# -*- coding: utf-8 -*-
__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.3.0"

#This is the list...
atomic_number_covalent ={
1:0.32,
10:0.71,
9:0.72,
8:0.73,
7:0.75,
6:0.77,
5:0.82,
4:0.9,
2:0.93,
18:0.98,
17:0.99,
16:1.02,
15:1.06,
14:1.11,
36:1.12,
35:1.14,
28:1.15,
34:1.16,
27:1.16,
29:1.17,
26:1.17,
25:1.17,
13:1.18,
24:1.18,
33:1.2,
32:1.22,
23:1.22,
3:1.23,
45:1.25,
44:1.25,
30:1.25,
31:1.26,
76:1.26,
77:1.27,
43:1.27,
75:1.28,
46:1.28,
74:1.3,
78:1.3,
42:1.3,
54:1.31,
22:1.32,
53:1.33,
73:1.34,
41:1.34,
47:1.34,
79:1.34,
52:1.36,
12:1.36,
50:1.41,
51:1.41,
92:1.42,
49:1.44,
21:1.44,
72:1.44,
40:1.45,
85:1.45,
83:1.46,
84:1.46,
82:1.47,
48:1.48,
81:1.48,
80:1.49,
11:1.54,
69:1.56,
71:1.56,
68:1.57,
67:1.58,
66:1.59,
65:1.59,
64:1.61,
39:1.62,
62:1.62,
61:1.63,
60:1.64,
90:1.65,
58:1.65,
59:1.65,
57:1.69,
70:1.74,
20:1.74,
63:1.85,
38:1.91,
56:1.98,
19:2.03,
37:2.16,
55:2.35,
}

class LowDimGroupFinderExc(Exception):
    pass

class WeirdStructureExc(LowDimGroupFinderExc):
    """
    """
    pass

class GroupOverTwoCellsNoConnectionsExc(LowDimGroupFinderExc):
    """
    Raised when the group expands over at least two cells, but no connection is found.
    """
    pass



class LowDimGroupFinder(object):
    def __init__(self, aiida_structure, **kwargs):
        """
        Takes an aiida_structure, analyses the structure and returns a lower dimensionality structure, if it can be found.

        :param cov_bond_margin: percentage which is added to the covalent
          bond length, the criterium which defines if atoms are bound or not.
        :param vacuum_space:
        :param supercell:
        :param target_dimensionality:
        """
        import ase
        import numpy as np
        self.params = { "cov_bond_margin" : 0.1,
                        "vacuum_space" : 1,
                        "max_supercell" : 2,
                        "min_supercell" : 2,
                        "full_periodicity": False,
                        "rotation": False,
                    }
        self.setup_builder(**kwargs)

        #starting with a 2x2x2 supercell size is increased until reaching max_supercell
        self.supercell_size = self.params["min_supercell"]

        self.aiida_structure = aiida_structure
        self.structure = self.aiida_structure.get_ase()
        self.n_unit = len(self.structure)
        self.supercell = self.structure.repeat(self.supercell_size)

        self._group_number = None
        self._low_dim_index = 0
        self._found_unit_cell_atoms = set([])

        #6 independent variables, don't forget to add new one to the get_group_data method

        self._groups = []
        self._unit_cell_groups = []
        self._atoms_in_one_cell = []
        self._connection_counter = []
        self._connected_positions = []
        self._vectors = []
        self._dimensionality = []

        self._reduced_ase_structures = []
        self.reduced_aiida_structures = []

    def setup_builder(self, **kwargs):
        """
        Changes the builder parameters.
        """
        for k, v in kwargs.iteritems():
            if k in self.params.keys():
                self.params[k] = v



    def _define_groups(self):
        """
        This function takes as parameter a bonding table with True on the place ixj if atom i and j are covalently bond together.
        It returns the different group found in the cell.
        """
        import time
        start_time = time.time()
        import numpy as np
        n_sc = len(self.supercell)
        #get distances between all the atoms
        coords = self.supercell.get_positions()
        dist = get_distances(coords, coords)

        cov_radius = []
        #do this directly in the cov_matrix (?)
        for i in range(n_sc):
            cov_radius.append(atomic_number_covalent[self.supercell.get_atomic_numbers()[i]])
        #covalent radius matrix, ij contains the sum of covalent radius of atom i and j multiplied by 1+self.params["cov_bond_margin"]
        cov_matrix = np.zeros((n_sc,n_sc))
        for i in range(n_sc):
            for j in range(i,n_sc):
                cov_matrix[i][j] = (cov_radius[i] + cov_radius[j])* (1 + self.params["cov_bond_margin"])
                if i != j:
                    cov_matrix[j][i] = cov_matrix[i][j]

        # True means that they are connected
        bond_table = dist - cov_matrix < 0

        set_dict = {}
        # for each site a set of the neighbouring ids
        for i in range(n_sc):
            set_dict[i] = set([])
            for j in range(n_sc):
                if bond_table[i][j]:
                    set_dict[i].add(j)

        #follow connections to make groups of connected atoms
        for k, v in set_dict.iteritems():
            visited = []
            update_set(set([k]), v, k, set_dict,visited)

        groups = []
        visited = []

        for k, v in set_dict.iteritems():
            if k not in visited:
                visited = visited + list(v)
                groups.append(sorted(list(v)))

        print "supercell_size {}, n_atoms {}, --- {} seconds ---".format(self.supercell_size, n_sc, time.time() - start_time)

        self._groups = sorted(groups, key=len, reverse=True)


    def _define_unit_cell_group(self):
        """
        Analyses the largest group defines which atoms of the group define the unit cell.
        unit_cell_sites are the corresponding periodic sites in the unit cell
        unit_cell_group -> reduced_unit_cell_group
        """
        import math

        group = self.groups[self._group_number]

        unit_cell_sites = set([])
        reduced_unit_cell_group = set([])
        for i in group:
            if i%self.n_unit not in unit_cell_sites:
                unit_cell_sites.add(i%self.n_unit)
                reduced_unit_cell_group.add(i)

        self._unit_cell_groups.append(sorted(list(reduced_unit_cell_group)))

        self._found_unit_cell_atoms.update(unit_cell_sites)

        if unit_cell_sites == reduced_unit_cell_group:
            self._atoms_in_one_cell.append(True)
        else:
            self._atoms_in_one_cell.append(False)

    def _define_number_of_connections(self):
        """
        The connection of a periodic site with its images in the 7 other cells (2x2x2 supercell) is checked.
        If there are no connection the function will return 1 and the structure is a molecule. 2 means an elongated structure.
        3 groups in <111> direction. 4 groups in <110> or <100> direction. And >4 it's all over connected, polymer/bulk/no groups.
        Could take the standard deviation of those sites, to make it even more accurate?

        :param group: Normally the biggest group is taken, but it works also with other groups of atoms.
        """
        group = self.groups[self._group_number]

        periodic_site_in_unit_cell = group[0]%self.n_unit
        counter = 0
        pos = []
        for i in range(self.supercell_size**3):
            if i*self.n_unit + periodic_site_in_unit_cell in group:
                counter = counter + 1
                pos.append(self.supercell.get_positions()[i*self.n_unit+periodic_site_in_unit_cell])

        self._connection_counter.append(counter)
        self._connected_positions.append(pos)


        if self._connection_counter == 1 and self.supercell_size < self.params["max_supercell"] and self._low_dim_index == 0:

            self.supercell_size = self.supercell_size + 1
            print "No connection found. Increasing supercell size to {}".format(self.supercell_size)
            #reset all the group data
            self._groups = []
            self._unit_cell_groups = []
            self._atoms_in_one_cell = []
            self._connection_counter = []
            self._connected_positions = []
            self._vectors = []
            self._dimensionality = []

            self.supercell = self.structure.repeat(self.supercell_size)

            self._define_number_of_connections()

    def _define_dimensionality(self):
        import numpy as np


        vectors = []
        for i in self.connected_positions[self._low_dim_index]:
            if i is not self.connected_positions[self._low_dim_index][0]:
                vectors.append(i - self._connected_positions[self._low_dim_index][0])
        self._dimensionality.append(np.linalg.matrix_rank(vectors))

        if self._dimensionality[self._low_dim_index] == 0:
            self._vectors.append([np.array([1,0,0]), np.array([0,1,0]), np.array([0,0,1])])

        elif self._dimensionality[self._low_dim_index] == 1:
            normal_vector1 = np.cross(vectors[0],[1,0,0])
            if np.linalg.norm(normal_vector1) < 0.000001:
                normal_vector1 = np.cross(vectors[0],[0,1,0])
            normal_vector2 = np.cross(vectors[0], normal_vector1)
            normal_vector1 = normal_vector1/np.linalg.norm(normal_vector1)
            normal_vector2 = normal_vector2/np.linalg.norm(normal_vector2)
            self._vectors.append([normal_vector1,normal_vector2, vectors[0]])

        elif self._dimensionality[self._low_dim_index] == 2:
            idx = find_shortest_vector(vectors)
            vector1 = vectors.pop(idx)
            idx = find_shortest_vector(vectors)
            vector2 = vectors.pop(idx)

            vector3 = np.cross(vector1,vector2)

            while np.linalg.norm(vector3) < 0.0000001:
                idx = find_shortest_vector(vectors)
                vector2 = vectors.pop(idx)
                vector3 = np.cross(vector1,vector2)

            vector3 = vector3/np.linalg.norm(vector3)
            self._vectors.append([vector1,vector2,vector3])

        elif self._dimensionality[self._low_dim_index] == 3:
            self._vectors.append(self.structure.cell)




    def _define_reduced_ase_structure(self):
        from ase import Atoms
        import numpy as np

        # find out minimum and maximum value in z
        # initialisation with first value ?
        min_z = None
        max_z = None
        min_x = None
        min_y = None
        max_x = None
        max_y = None

        symbols =[]

        positions = []

    # 3 Dimensional --> return first structuree
        if self.dimensionality[self._low_dim_index] == 3:
            self._reduced_ase_structures.append(self.structure)
            return
        elif self.dimensionality[self._low_dim_index]  == 2:

            for i in self.unit_cell_groups[self._low_dim_index] :
                        #get positions from supercell?
                positions.append([self.supercell.positions[i][0],self.supercell.positions[i][1],self.supercell.positions[i][2]])
                symbols.append(self.supercell.get_chemical_symbols()[i])

                if min_z is None or min_z > positions[-1][2]:
                    min_z = positions[-1][2]
                if max_z is None or max_z < positions[-1][2]:
                    max_z = positions[-1][2]

            positions = np.array(positions)

            positions[:,2] = positions[:,2] - min_z + self.params["vacuum_space"]/2

            self._vectors[self._low_dim_index][2] = self._vectors[self._low_dim_index][2] * (self.params["vacuum_space"] + max_z-min_z)

            pbc = [True, True, False]


        elif self.dimensionality[self._low_dim_index] == 1:
            for i in self.unit_cell_groups[self._low_dim_index]:
                positions.append([self.supercell.positions[i][0],self.supercell.positions[i][1],self.supercell.positions[i][2]])
                symbols.append(self.supercell.get_chemical_symbols()[i])

                if min_x is None or min_x > positions[-1][0]:
                    min_x = positions[-1][0]
                if max_x is None or max_x < positions[-1][0]:
                    max_x = positions[-1][0]
                if min_y is None or min_y > positions[-1][1]:
                    min_y = positions[-1][1]
                if max_y is None or max_y < positions[-1][1]:
                    max_y = positions[-1][1]

            positions = np.array(positions)

            positions[:,0] = positions[:,0] - min_x + self.params["vacuum_space"]/2
            positions[:,1] = positions[:,1] - min_y + self.params["vacuum_space"]/2

            self._vectors[self._low_dim_index][0] = self._vectors[self._low_dim_index][0] * (self.params["vacuum_space"] + max_x-min_x)
            self._vectors[self._low_dim_index][1] = self._vectors[self._low_dim_index][1] * (self.params["vacuum_space"] + max_y-min_y)


            pbc =[False, False, True]

        elif self.dimensionality[self._low_dim_index] == 0:

            for i in self.unit_cell_groups[self._low_dim_index]:
                positions.append([self.supercell.positions[i][0],self.supercell.positions[i][1],self.supercell.positions[i][2]])
                symbols.append(self.supercell.get_chemical_symbols()[i])


                if min_z is None or min_z > positions[-1][2]:
                    min_z = positions[-1][2]
                if max_z is None or max_z < positions[-1][2]:
                    max_z = positions[-1][2]
                if min_x is None or min_x > positions[-1][0]:
                    min_x = positions[-1][0]
                if max_x is None or max_x < positions[-1][0]:
                    max_x = positions[-1][0]
                if min_y is None or min_y > positions[-1][1]:
                    min_y = positions[-1][1]
                if max_y is None or max_y < positions[-1][1]:
                    max_y = positions[-1][1]

            positions = np.array(positions)

            pbc =[False, False, False]

            positions[:,0] = positions[:,0] - min_x + self.params["vacuum_space"]/2
            positions[:,1] = positions[:,1] - min_y + self.params["vacuum_space"]/2
            positions[:,2] = positions[:,2] - min_z + self.params["vacuum_space"]/2

            self._vectors[self._low_dim_index][0] = self._vectors[self._low_dim_index][0] * (self.params["vacuum_space"] + max_x-min_x)
            self._vectors[self._low_dim_index][1] = self._vectors[self._low_dim_index][1] * (self.params["vacuum_space"] + max_y-min_y)
            self._vectors[self._low_dim_index][2] = self._vectors[self._low_dim_index][2] * (self.params["vacuum_space"] + max_z-min_z)


        else:
            raise WeirdStructureExc("No dimensionality")



        if self.params["full_periodicity"] == True:
            pbc = [True,True,True]

        reduced_ase_structure = Atoms(cell=self._vectors[self._low_dim_index],pbc=pbc, symbols=symbols, positions=positions)

        #to wrap positions into the unit cell (?)
        reduced_ase_structure.set_positions(reduced_ase_structure.get_positions(wrap=True))

        if self.params["rotation"] == True:
            reduced_ase_structure = self._rotate_ase_structure(reduced_ase_structure)

        self._reduced_ase_structures.append(reduced_ase_structure)

    def _define_reduced_ase_structures(self):

        test = set(range(self.n_unit))

        for idx, group in enumerate(self.groups):
            #checks if all atoms of the original unit cells have been allocated to a group
            if self._found_unit_cell_atoms == test:
                break
            self._group_number = idx

            print idx

            unit_cell_group = {i % self.n_unit for i in group}

            # if the atoms corresponding to the group are only a periodic replica of an existing low dimensionality
            # group, they are skipped and the next group is analysed..
            if unit_cell_group.issubset(self._found_unit_cell_atoms):

                continue
            else:
                print unit_cell_group
                self._define_reduced_ase_structure()
                self._low_dim_index = self._low_dim_index + 1
                print self._low_dim_index
        self._low_dim_index = self._low_dim_index -1








    def _define_reduced_aiida_structures(self):
        from aiida.orm import DataFactory
        if not self._reduced_ase_structures:
            self._define_reduced_ase_structures()
        S = DataFactory("structure")

        self.reduced_aiida_structures = []
        for i in self._reduced_ase_structures:
            self.reduced_aiida_structures.append(S(ase=i))


    def _rotate_ase_structure(self,asestruc):
        """
        Rotates the third vector in z-axis and the first vector in x-axis. Layer -> xy-plane, wire -> z-direction
        """
        import ase
        asestruc.rotate(v=asestruc.cell[2],a=[0,0,1],center='COP', rotate_cell = True)
        asestruc.rotate(v=asestruc.cell[0],a=[1,0,0],center='COP', rotate_cell = True)
        return asestruc




    @property
    def dimensionality(self):
        """
        uses rank of vector matrix between connected positions to get the dimensionality
        """
        if len(self._dimensionality) <= self._low_dim_index:
            self._define_dimensionality()
        return self._dimensionality


    @property
    def groups(self):
        if not self._groups:
            self._define_groups()
        return self._groups

    @property
    def biggest_group(self):
        if not self._groups:
            self._define_groups()

        return self._groups[0]

    @property
    def unit_cell_groups(self):
        if len(self._unit_cell_groups) <= self._low_dim_index:
            self._define_unit_cell_group()

        return self._unit_cell_groups


    @property
    def number_of_connections(self):
        if len(self._connection_counter) <= self._low_dim_index:
            self._define_number_of_connections()
        return self._connection_counter

    @property
    def connected_positions(self):
        if len(self._connection_counter) <= self._low_dim_index:
            self._define_number_of_connections()
        return self._connected_positions

    @property
    def vectors(self):
        if not self._vectors:
            self._define_number_of_connections()
        return self._vectors



    def _get_reduced_ase_structures(self):
        if not self._reduced_ase_structures:
            self._define_reduced_ase_structures()
        return self._reduced_ase_structures

    def get_reduced_aiida_structures(self):
        if not self.reduced_aiida_structures:
            self._define_reduced_aiida_structures()
        return self.reduced_aiida_structures

    def get_group_data(self):
        a = self.get_reduced_aiida_structures()
        return {#"groups": self.groups,
                "biggest_group": self.biggest_group,
                "unit_cell_group": self.unit_cell_groups,
                "number_of_connections": self.number_of_connections,
                #"connected_positions": self.connected_positions,
                "dimensionality": self.dimensionality,
                }


def find_shortest_vector(array):
    import numpy as np
    idx = np.array([np.linalg.norm(vector) for vector in array]).argmin()
    return idx

def update_set(set1, set2, k, set_dict, visited):
    """
    Recursive function that puts the ids of all atoms that are somehow linked together into the same set.
    """
    for i in (set2 - set1):
        if i not in visited:
            visited.append(i)
            set0 = set2.copy()
            set_dict[k].update(set_dict[i])
            update_set(set0,set_dict[k],k, set_dict,visited)

def get_distances(ccoord1, ccoord2):
    """
    Get the distances between to lists of cartesian coordinates. Position ixj contains distance between atom i and atom j.
    """
    import numpy as np
    matrix_list = (ccoord1[:, None, :] - ccoord2[None, :, :]) ** 2
    return np.sum(matrix_list, axis=-1) ** 0.5







if __name__ == '__main__':
    import aiida.tools.lowdimgroupfinder
    import numpy as np

    from aiida.orm import DataFactory
    from aiida import load_dbenv
    load_dbenv()
    S = DataFactory("structure")
    import ase.io
    graph_ase = ase.io.read("../../cif/PdS2.cif")
    graph_aiida = S(ase=graph_ase)

    test = aiida.tools.lowdimgroupfinder.LowDimGroupFinder(aiida_structure = graph_aiida, vacuum_space=20, rotation=True)
    #red_struc = test.get_reduced_aiida_structure()
    red_ase = test._define_reduced_ase_structure()

    ase.io.write("PdS2_2D.cfg",red_ase, format="cfg")
    ase.io.write("PdS2_3D.cfg",graph_ase,format="cfg")

    print red_ase.cell
    print red_ase.get_positions()



    print test._check_reduced_aiida_structure

    test = aiida.tools.lowdimgroupfinder.LowDimGroupFinder(aiida_structure = graph_aiida, vacuum_space=1, rotation=True, min_supercell=3, max_supercell=3)
    #red_struc = test.get_reduced_aiida_structure()
    red_ase = test._define_reduced_ase_structure()

    print red_ase.cell
    print red_ase.get_positions()

    print test.get_group_data()




