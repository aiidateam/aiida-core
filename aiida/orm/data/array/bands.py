# -*- coding: utf-8 -*-
"""
This module defines the classes related to band structures or dispersions
in a Brillouin zone, and how to operate on them.
"""

from aiida.orm.data.array.kpoints import KpointsData
import numpy

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

#TODO: set and get bands could have more functionalities: how do I know the number of bands for example?
#TODO: a function that exports to a file an array that can be plotted with xmgrace or gnuplot

class BandsData(KpointsData):

    def set_kpointsdata(self,kpointsdata):
        """
        Load the kpoints from a kpoint object.
        :param kpointsdata: an instance of KpointsData class
        """
        if not isinstance(kpointsdata,KpointsData):
            raise ValueError("kpointsdata must be of the KpointsData class")
        try:
            self.cell = kpointsdata.cell
        except AttributeError:
            pass
        try:
            self.pbc=kpointsdata.pbc
        except AttributeError:
            pass
        try:
            self.bravais_lattice = kpointsdata.bravais_lattice
        except AttributeError:
            pass
        try:
            self.set_kpoints( kpointsdata.get_kpoints() )
        except AttributeError:
            pass
        try:
            self.labels = kpointsdata.labels
        except (AttributeError,TypeError):
            pass
        
    def set_bands(self,bands):
        """
        Set an array of band energies of dimension (nkpoints x nbands).
        Kpoints must be set in advance. Can contain floats or None.
        """
        #TODO: more checks here
        try:
            kpoints = self.get_kpoints()
        except AttributeError:
            raise AttributeError("Must first set the kpoints, then the bands")
        
        if len(bands.shape)!=2:
            raise ValueError("bands must be an array of shape 2"
                             "(must have rows and columns) found instead {}"
                             .format(len(bands.shape))) 
        
        if bands.shape[0] != len(kpoints):
            raise ValueError("There must be energy values for every kpoint") 
        
        for i in range(bands.shape[0]):
            for j in range(bands.shape[1]):
                if bands[i,j] is not None:
                    try:
                        float(bands[i,j])
                    except (TypeError,ValueError):
                        raise ValueError("The bands array can only contain "
                                         "float or None values")
        
        self.set_array('bands',bands)

    def get_bands(self):
        """
        Returns an array (nkpoints x num_bands) of energies.
        """
        try:
            return self.get_array('bands')
        except KeyError:
            raise AttributeError("No stored bands has been found")
         
    def export(self,path,fileformat=None,overwrite=False,comments=True):
        """
        Export the bands to a file.
        :param path: absolute path of the file to be created
        :fileformat: format of the file created. If None, tries to use the 
                     extension of path to understand the correct one.
        :param overwrite: if set to True, overwrites file found at path. Default=False
        :param comments: if True, append some extra informations at the 
                beginning of the file.
                
        Note: this function will NOT produce nice plots if:
              - there is no path of kpoints, but a set of isolated points
              - the path is not continuous AND no labels are set  
        """
        import os
        from aiida import get_file_header
        
        if not path:
            raise ValueError("Path not recognized")
        
        if os.path.exists(path) and not overwrite:
            raise OSError("A file was already found at {}".format(path))
        
        if fileformat is None:
            extension = os.path.splitext(path)[1].split('.')[1]
            if not extension:
                raise ValueError("Cannot recognized the fileformat from the "
                                 "extension")
            fileformat = extension
            if extension == 'dat':
                fileformat = 'dat_1'
        
        preparer_name = "_prepare_" + fileformat
        
        # load the x and y's of the graph
        bands = self.get_bands()
        # here I build the x distances on the graph
        try:
            kpoints = self.get_kpoints(cartesian=True)
        except AttributeError:
            kpoints = self.get_kpoints()
        # I take advantage of the path to recognize discontinuities
        try:
            labels = self.labels
            labels_indices = [i[0] for i in labels]
        except AttributeError:
            labels = []
            labels_indices = []
        # since I can have discontinuous paths, I set on those points the distance to zero
        # as a result, where there are discontinuities in the path, 
        # I have two consecutive points with the same x coordinate
        distances = [0.] + [ numpy.linalg.norm( kpoints[i]-kpoints[i+1] ) if not  
                      (i in labels_indices and i+1 in labels_indices) else 0. 
                      for i in range(len(kpoints)-1) ]
        x = [ float(sum(distances[:i])) for i in range(len(distances)) ]

        # transform the index of the labels in the coordinates of x
        the_labels = [ (x[i[0]],i[1]) for i in labels ] 

        plot_info = {}
        plot_info['x'] = x
        plot_info['y'] = bands
        plot_info['labels'] = the_labels
        plot_info['filename'] = path
        if extension == 'agr':
            plot_info['filename'] = os.path.splitext(path)[0] + '.dat'

        # generic info
        if comments:
            filetext = []
            #filetext.append("{}".format(get_file_header()))
            filetext.append("#\tpoints\tbands")
            filetext.append("#\t{}\t{}".format(*bands.shape))
            filetext.append("# \tlabel\tpoint")
            for i,l in enumerate(labels):
                filetext.append( "#\t{}\t{:.8f}".format(l[1],x[i]) )
            filetext = get_file_header() + "#\n" + "\n".join(filetext) + "\n\n"
        else:
            filetext=""
            
        try:
            newfiletext,extra_files = getattr(self,preparer_name)(plot_info)
            filetext += newfiletext
        except AttributeError:
            raise
#            raise ValueError("Format {} is not valid".format(fileformat))
        
        if extra_files is not None:
            for k,v in extra_files.iteritems():
                if os.path.exists(k) and not overwrite:
                    raise OSError("A file was already found: {}".format(k) )
                else:
                    with open( k,"w" ) as f:
                        f.write(v)
        
        with open(path,'w') as f:
            f.write(filetext) 
        
    def get_export_formats(self):
        names = dir(self)
        return [ i.split('_prepare_')[1] for i in names if i.startswith('_prepare_') ]
        
    def _prepare_agr(self,plot_info):
        """
        Prepare two files, data and batch, to be plot with xmgrace as:
        xmgrace -batch file.dat
        """
        bands = plot_info['y']
        x = plot_info['x']
        labels = plot_info['labels']
        
        num_labels = len(labels)
        num_bands = bands.shape[1]

        # axis limits
        y_max_lim = bands.max()
        y_min_lim = bands.min()
        x_min_lim = min(x) # this isn't a numpy array, but a list
        x_max_lim = max(x)
        
        # first prepare the xy coordinates of the sets
        raw_data,_ = self._prepare_dat_2(plot_info)
                
        # add the xy coordinates of the vertical lines
        for l in labels:
            new_block = ["{}\t{}".format(l[0],y_min_lim) ]
            new_block.append( "{}\t{}".format(l[0],y_max_lim) )
            new_block.append("")
            raw_data += "\n".join(new_block)
        
        filexy_name = plot_info['filename']
        
        batch = []
        batch.append( 'READ XY "{}"'.format(filexy_name) )
        
        # axis limits
        batch.append("world {}, {}, {}, {}".format(x_min_lim,y_min_lim,x_max_lim,y_max_lim) )

        # axis label        
        batch.append( 'yaxis label "Dispersion"' )

        # axis ticks
        batch.append( 'xaxis  tick place both')
        batch.append( 'xaxis  tick spec type both')
        batch.append( 'xaxis  tick spec {}'.format(len(labels)))
        # set the name of the special points
        for i,l in enumerate(labels):
            batch.append( "xaxis  tick major {}, {}".format(i,l[0]) )
            batch.append( 'xaxis  ticklabel {}, "{}"'.format(i,l[1]) )

        # minor graphical tweak
        batch.append( "yaxis  tick minor ticks 3" )
        batch.append("frame linewidth 2.0")
        
        # use helvetica fonts
        batch.append( 'map font 4 to "Helvetica", "Helvetica"' )
        batch.append("yaxis  label font 4")
        batch.append("xaxis  label font 4")

        # set color and linewidths of bands
        for i in range(num_bands):
            batch.append( "s{} line color 1".format(i) )
            batch.append( "s{} linewidth 1".format(i) )

        # set color and linewidths of bands
        for i in range(num_bands,num_bands+num_labels):
            batch.append( "s{} line color 1".format(i) )
            batch.append( "s{} linewidth 2".format(i) )
        
        batch_data = "\n".join(batch) + "\n"
        extra_files = {"batch.dat":batch_data}
        
        return raw_data, extra_files


    def _prepare_dat_1(self,plot_info):
        """
        Write an N x M matrix. First column is the distance between kpoints,
        The other columns are the bands. Header contains number of kpoints and 
        the number of bands (commented).
        """
        bands = plot_info['y']
        x = plot_info['x']
        
        return_text = []
        
        for i in zip(x,bands):
            line = [ "{:.8f}".format(i[0]) ] + [ "{:.8f}".format(j) for j in i[1] ]
            return_text.append( "\t".join( line ) )
        
        return "\n".join(return_text) + '\n', None
    
    def _prepare_dat_2(self,plot_info):
        """
        Format suitable for gnuplot using blocks.
        Columns with x and y (path and band energy). Several blocks, separated
        by two empty lines, one per energy band.
        """
        bands = plot_info['y']
        x = plot_info['x']
        
        return_text = []
        
        the_bands = numpy.transpose(bands)
        
        for b in the_bands:
            for i in zip(x,b):
                line = [ "{:.8f}".format(i[0]) , "{:.8f}".format(i[1]) ]
                return_text.append( "\t".join( line ) )
            return_text.append("")
            return_text.append("")
        
        return "\n".join(return_text), None

