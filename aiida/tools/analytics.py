'''
Created on Oct 30, 2013

@author: riki
'''

RyToBhor = 0.52917720859

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
        
        elems = self.struct.get_elements()
        self.ordering = [None]*len(elems)
         
        count = 0
        for k in range(len(elems)):
            self.ordering[k] = []
            for s in range(len(self.struct.sites)):
                if str(self.struct.sites[s].kind) == elems[k]:
                    self.ordering[k].append(s)
                    count+=1
         
    def append(self, step, time, cell, pos, data, vel=None):
        
        self.steps.append(step)
        self.steps.append(time)
        self.cells.append(cell)
        self.pos.append(pos)
        self.datas.append(data)
        
        if vel:
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
                
                self.df = pd.DataFrame(self.datas, columns=self.datas_attrs)
                return self.df
            
        elif name in self.datas_attrs:
            import numpy as np
            
            id = self.datas_attrs.index(name)
            return np.array(self.datas)[:,id]
            
        else:
            # Default behaviour
            return object.__getattribute__(self, name)
    
    def plot_dynamics_data(self, start=0):
        
        import matplotlib.pyplot as plt
        
        ax1 = plt.subplot2grid((2,2), (0,0), colspan=2)
        ax2 = plt.subplot2grid((2,2), (1,0))
        ax3 = plt.subplot2grid((2,2), (1,1))
        
        self.df[start:len(self.df)][["etot", "econt", "econs"]].plot(ax=ax1)
        ((self.df[start:len(self.df)].etot-self.df[start:len(self.df)].econs)/(self.df[start:len(self.df)].econs-self.df[start:len(self.df)].econt)).plot(ax=ax2)
        self.df.tempp[start:len(self.df)].plot(ax3)
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
    
    reading_pos = False
    
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
    if vel: vel_all  = import_array(dir+os.sep+prefix+".vel")
    cell_all = import_array(dir+os.sep+prefix+".cel", mul=RyToBhor)
    evp      = import_table(dir+os.sep+prefix+".evp")
    
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
        
        trajectories_this.append(pos_all[i].get_step(), pos_all[i].get_time(), cell_all[i].get_array(), pos_all[i].get_array(), evp[i])
    
    trajectories_all.append(trajectories_this)
            
    return trajectories_all
      
