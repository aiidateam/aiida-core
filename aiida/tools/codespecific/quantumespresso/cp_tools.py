# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This module contains some functions to manage inputs and outputs from the
Car-Parrinello cp.x code of Quantum ESPRESSO.
Currently unmantained, may be removed or reused at any time!
"""


RyToBhor         = 0.52917720859
k_boltzmann_si   = 1.3806504E-23
hartree_si       = 4.35974394E-18
electronmass_si  = 9.10938215E-31
amu_si           = 1.660538782E-27
k_boltzmann_au   = k_boltzmann_si / hartree_si

autoev           = hartree_si / electronmass_si
rytoev           = autoev / 2.0
amu_au           = amu_si / electronmass_si

def generate_cp_velocities(s, temp, force_kind_order = False, seed=None):
    
    import numpy as np
    import aiida.orm.data.structure as struct
    
    if not isinstance(s, struct.StructureData):
        return
    
    masses   = []
    elements = []
    kinds = s.kinds
    
    if force_kind_order:
        for k in kinds:
            for s in s.sites:
                if s.kind == k.name:
                    elements.append(k.name)
                    masses.append(k.mass)
    else:
        for s in s.sites:
            for k in kinds:
                if s.kind == k.name:
                    elements.append(k.name)
                    masses.append(k.mass)
    
    vi = MaxwellBoltzmannDistribution(np.array(masses), temp, seed=seed)
    
    return zip(elements, vi[:])

class StepArray(object):
    
    def __init__(self):
    
        self.step = 0
        self.time = 0
        self.array  = []
    
    def set_step(self, _step):
        self.step = _step
    
    def set_time(self, _time):
        self.time = _time
        
    def set_array(self, _array):
        self.array = _array
    
    def get_step(self):
        return self.step
    
    def get_time(self):
        return self.time
    
    def get_array(self):
        return self.array

class SimpleTrajectory(object):
    
    def __init__(self, aiida_struct):
        
        self.struct = aiida_struct
        self.generate_kind_ordering()
        
        self.datas_attrs = ["n","ekinc","temph","tempp","etot","enthal","econs","econt","a","b","c"]
        
        self.cells = []
        self.pos   = []
        self.steps = []
        self.times = []
        self.datas = []
        self.velocities = []
    
    def generate_kind_ordering(self):
        
        elems = self.struct.get_kind_names()
        self.ordering = [None]*len(elems)
         
        count = 0
        for k in range(len(elems)):
            self.ordering[k] = []
            for s in range(len(self.struct.sites)):
                if str(self.struct.sites[s].kind_name) == elems[k]:
                    self.ordering[k].append(s)
                    count+=1
        
        print self.ordering
        
    def append(self, step, time, cell, pos, data, vel=None):
        
        self.steps.append(step)
        self.times.append(time)
        self.cells.append(cell)
        self.pos.append(pos)
        self.datas.append(data)
        
        if vel is not None:
            self.velocities = vel
        
    def get_snapshot(self, step): 
        
        id = self.steps.index(step)
        
        if id==-1:
            return None
        return self.cells[id], self.pos[id], self.datas[id]
        
    def get_steps(self):
        return self.step
    
    def __getattr__(self, name):
        
        import pandas as pd
        if name=="df":
            
            if hasattr(self, 'df'):
                return self.df
            else:
                
                self.df = pd.DataFrame(self.datas, columns=self.datas_attrs, index=self.times)
                return self.df
            
        elif name in self.datas_attrs:
            import numpy as np
            
            id = self.datas_attrs.index(name)
            return np.array(self.datas)[:,id]
            
        else:
            # Default behaviour
            return object.__getattribute__(self, name)
    
    def generate_species_data(self):
        
        import ase.data
        import numpy as np
        
        ekins = {}
        et    = {}
        all_temp = []
        
        _masses = self.struct.get_ase().get_masses()
        _at_nums = self.struct.get_ase().get_atomic_numbers()
        for t in range(len(self.times)):
            
            masses = np.take(_masses, np.concatenate(self.ordering))
            all_temp.append(getIonT_K(masses,self.velocities[t].get_array()))
            
            for i in range(len(self.ordering)):
            
                at_num   = _at_nums[self.ordering[i][0]]
                w_name   = ase.data.chemical_symbols[at_num]
            
                for at in range(len(self.ordering[i])):
                
                    ion_key        = w_name+"_"+str(self.ordering[i][at])
                    
                    if "ekin_"+ion_key not in ekins: 
                        ekins["ekin_"+ion_key] = []
                    
                    if "temp_"+ion_key not in et:
                        et["temp_"+ion_key]    = []
                    
                    mi  = np.array([_masses[self.ordering[i][at]]])
                    vi  = np.array([self.velocities[t].get_array()[self.ordering[i][at]]])
                    
                    eki = getIonEkin_SI(mi,vi)
                    ekins["ekin_"+ion_key].append(eki)
                    
                    eti = getIonT_K(mi,vi)
                    et["temp_"+ion_key].append(eti)
            
        
        for k in ekins.keys():
            self.df[k] = ekins[k]
        
        for k in et.keys():
            self.df[k] = et[k]
        
        self.df['all_temp'] = all_temp
    
    def plot_dynamics_data(self, start=0):
        
        import matplotlib.pyplot as plt
        
        ax1 = plt.subplot2grid((2,2), (0,0), colspan=2)
        ax2 = plt.subplot2grid((2,2), (1,0))
        ax3 = plt.subplot2grid((2,2), (1,1))
        
        self.df[start:len(self.df)][["etot", "econt", "econs"]].plot(ax=ax1)
        ((self.df[start:len(self.df)].etot-self.df[start:len(self.df)].econs)/(self.df[start:len(self.df)].econs-self.df[start:len(self.df)].econt)).plot(ax=ax2)
        self.df.tempp[start:len(self.df)].plot(ax3)
        plt.show()
    
    def plot_temp_data(self, start=0):
        
        import matplotlib.pyplot as plt
        import ase.data
        
        ax1 = plt.subplot2grid((2,2), (0,0), colspan=2)
        ax2 = plt.subplot2grid((2,2), (1,0))
        ax3 = plt.subplot2grid((2,2), (1,1))
        
        ekins = []
        et    = []
        
        for i in range(len(self.ordering)):
            at_num   = self.struct.get_ase().get_atomic_numbers()[self.ordering[i][0]]
            w_name   = ase.data.chemical_symbols[at_num]
            
            for at in range(len(self.ordering[i])):
                ion_key        = w_name+"_"+str(self.ordering[i][at])
                
                if "ekin_"+ion_key not in self.df:
                    print "Generating"
                    self.generate_species_data()
                    
                ekins.append("ekin_"+ion_key)
                et.append("temp_"+ion_key)
                
        self.df[et].plot(ax=ax1, legend=False)
        self.df[et].mean().plot(kind='bar', ax=ax2, yerr=self.df[et].std())
        self.df.all_temp.plot(ax=ax3)
        self.df.tempp.plot(ax=ax3)
        
        plt.show()
    
    def plot_temp_data_by_species(self, start=0):
        
        import matplotlib.pyplot as plt
        import ase.data
        
        specs = len(self.ordering)
        
        axes = []
        axes_2 = []
        for i in range(specs):
            axes.append(plt.subplot2grid((specs,2), (i,0)))
            axes_2.append(plt.subplot2grid((specs,2), (i,1)))
        
        for i in range(len(self.ordering)):
            
            et    = []
            
            at_num   = self.struct.get_ase().get_atomic_numbers()[self.ordering[i][0]]
            w_name   = ase.data.chemical_symbols[at_num]
            
            for at in range(len(self.ordering[i])):
                ion_key        = w_name+"_"+str(self.ordering[i][at])
                et.append("temp_"+ion_key)
                
            
            self.df[et].plot(ax=axes[i], legend=False)
            (self.df[et].sum(axis=1)/len(self.ordering[i])).plot(ax=axes_2[i], legend=False)
            
        plt.show()
        
    def export_to_vft(self, fname=None):
        
        
        #f = open(fname, "wb")
        import ase.data
        import StringIO
        import numpy as np
        import ase.lattice.spacegroup.cell as cell
        
        def shrink_list(nums):
        
            start = nums[0]
            end   = nums[0]
            
            output = ""
            
            step = 1
            for i in range(1, len(nums)):
                
                if nums[i] == start+step:
                    end = nums[i]
                    step+=1
                else:
                    end = nums[i-1]
                    
                    if start==end:
                        output+=("" if output=="" else ",")+str(start)
                    else:
                        output+=("" if output=="" else ",")+str(start)+":"+str(end)
                    
                    start = nums[i]
                    end   = nums[i]
                    step=1
                
                if (i==len(nums)-1):
                    
                    if start==end:
                        output+=("" if output=="" else ",")+str(start)
                    else:
                        output+=("" if output=="" else ",")+str(start)+":"+str(end)
                
            return output
        
        output = StringIO.StringIO()
        
        output.write("# STRUCTURE BLOCK\n")
        #atom 0,2,4      radius 1.0 name N
        
        for t in range(len(self.ordering)):
            
            w_ids    = shrink_list(self.ordering[t])
            at_num   = self.struct.get_ase().get_atomic_numbers()[self.ordering[t][0]]
            
            w_radius = ase.data.vdw.vdw_radii[at_num]
            w_name   = ase.data.chemical_symbols[at_num]
            if np.isnan(w_radius):    
                w_radius = ase.data.covalent_radii[at_num]
                
            
            output.write("atom {0} radius {1} name {2} atomicnumber {3}\n".format(w_ids, w_radius, w_name, t))
        
        output.write("# TIMESTEP BLOCKS\n")
        
        for i in range(len(self.pos)):
            
            w_cell = " ".join(["{0:.8f}".format(ap) for ap in cell.cell_to_cellpar(self.cells[i])])
            
            output.write("timestep\n")
            output.write("pbc {0}\n".format(w_cell))
            
            for kind_order in self.ordering:
                
                for o in kind_order:
                    ordered_pos = self.pos[i][o]
                    a_pos       = " ".join(["{0:.8f}".format(ap) for ap in ordered_pos])
                    output.write("{0}\n".format(a_pos))
           
        try:
            if not fname == None:
                f = open(fname,'wb')
                f.write(output.getvalue())
                f.close()
            else:
                return output.getvalue()
        except:
            return None
        finally:
            output.close()
                 
        

def import_table(fname):
    
    f = open(fname)
    
    data = []
    
    while 1:
        
        ## Buffer read
        lines = f.readlines(1000)
        if not lines:
            break
        for line in lines:
            parts = line.split()
            
            if len(parts)==11:
                data.append([float(p) for p in parts])
    
    f.close()
    
    return data
            
def import_array(fname, mul=1.0):
    
    f = open(fname)
    
    d_step = 0
    d_time = 0
    
    pos_all = []
    pos_this = []
    
    while 1:
        
        ## Buffer read
        lines = f.readlines(1000)
        if not lines:
            break
        for line in lines:
            parts = line.split()
            
            if len(parts)==2:
            
                if len(pos_this)>0:
                    nsp = StepArray()
                    nsp.set_step(d_step)
                    nsp.set_time(d_time)
                    nsp.set_array(pos_this)
                    pos_all.append(nsp)
                
                d_step = int(parts[0])
                d_time = float(parts[1])
                pos_this = []
            elif len(parts)==3:
                pos_this.append([float(p)*mul for p in parts])
        
    if d_time>pos_all[-1].get_time():
        nsp = StepArray()
        nsp.set_step(d_step)
        nsp.set_time(d_time)
        nsp.set_array(pos_this)
        pos_all.append(nsp)
        
    f.close()
    
    return pos_all

def import_cp(s, dir, prefix, vel=False):
    
    import aiida.orm.data.structure as struct
    import ase.atoms as atoms
    import os
    
    if not isinstance(s, struct.StructureData):
        print "Not an aiida structure"
        return
        
#     if not isinstance(s, struct.StructureData):
#         return
#     
    pos_all  = import_array(dir+os.sep+prefix+".pos", mul=RyToBhor)
    cell_all = import_array(dir+os.sep+prefix+".cel", mul=RyToBhor)
    evp      = import_table(dir+os.sep+prefix+".evp")
    
    vel_all = None
    if vel: vel_all  = import_array(dir+os.sep+prefix+".vel")
    
    old_step = 0
    trajectories_all = []
    trajectories_this = SimpleTrajectory(s)
    
    shift = 0
    
    for i in range(0, len(pos_all)):
        
        if (i+shift>=len(pos_all)):
            break
        
        while not pos_all[i+shift].get_step()==cell_all[i+shift].get_step() or \
           not pos_all[i+shift].get_time()==cell_all[i+shift].get_time() or \
           not pos_all[i+shift].get_step()==evp[i][0]:
            
            shift+=1
            print "Files not synced, trying to add some shit to pos, cel and vel {0}".format(shift)
            
            if (i+shift>=len(pos_all)):
                print "Something went wrong, files are not synced at {0} even with shift".format(i)
                break
            
        new_step = pos_all[i].get_step()
        if (new_step<=old_step):
            trajectories_all.append(trajectories_this)
            trajectories_this = SimpleTrajectory(s)
        
        trajectories_this.append(pos_all[i].get_step(), pos_all[i].get_time(), cell_all[i].get_array(), pos_all[i].get_array(), evp[i], vel=vel_all)
            
    trajectories_all.append(trajectories_this)
            
    return trajectories_all


def getIonEkin_SI(mi, vi):
    
    import numpy as np
    conv = amu_si/electronmass_si
    return 0.5 * np.dot(mi*conv, np.sum(np.square(vi), axis=1))

def getIonT_K(mi, vi):
    
    import numpy as np
    conv = amu_si/electronmass_si
    return 0.5 * np.dot(mi*conv, np.sum(np.square(vi), axis=1)) / (len(mi)) / (1.5*k_boltzmann_au)

def MaxwellBoltzmannDistribution(masses_amu, temp, kb=k_boltzmann_au, seed=None): 
        
        import numpy as np
            
        mi     = masses_amu*amu_au
            
        if seed is not None: np.random.seed(seed)
    
        ri     = np.random.standard_normal((len(mi), 3))
        vi     = ri * np.sqrt((kb * temp)/(mi[:, np.newaxis]))
        T0     = getIonT_K(mi, vi)
        gamma  = temp / T0
        vi     = vi * np.sqrt(gamma/3.0)
        
        return vi
    