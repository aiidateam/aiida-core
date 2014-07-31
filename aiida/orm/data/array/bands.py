# -*- coding: utf-8 -*-
"""
This module defines the classes related to band structures or dispersions
in a Brillouin zone, and how to operate on them.
"""

from aiida.orm.data.array.kpoints import KpointsData
import numpy
from string import Template

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
            filetext.append( "# Dumped from BandsData UUID={}"
                             .format(self.uuid) )
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
        
    def _prepare_agr_batch(self,plot_info):
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

    def _prepare_agr(self,plot_info):
        """
        Prepare an xmgrace agr file
        """
        # load the x and y of every set
        bands = plot_info['y']
        x = plot_info['x']
        the_bands = numpy.transpose(bands)
        labels = plot_info['labels']
        num_labels = len(labels)

        print labels

        # axis limits
        y_max_lim = the_bands.max()
        y_min_lim = the_bands.min()
        x_min_lim = min(x) # this isn't a numpy array, but a list
        x_max_lim = max(x)

        # prepare xticks labels
        sx1 = ""
        for i,l in enumerate(labels):
            sx1 += agr_single_xtick_template.substitute(index = i,
                                                     coord = l[0],
                                                     name = l[1],
                                                     )
        xticks = agr_xticks_template.substitute(num_labels = num_labels,
                                       single_xtick_templates = sx1,
                                       )

        # build the arrays with the xy coordinates
        all_sets = []
        for b in the_bands:
            this_set = ""
            for i in zip(x,b):
                line = "{:.8f}".format(i[0]) + '\t' + "{:.8f}".format(i[1]) +"\n"
                this_set += line
            all_sets.append(this_set)
        
        set_descriptions = ""
        for i,this_set in enumerate(all_sets):
            width = str(2.0) 
            set_descriptions += agr_set_description_template.substitute(
                                        set_number=i,
                                        linewidth = width
                                        )
        
        graphs = agr_graph_template.substitute(x_min_lim=x_min_lim, 
                                               y_min_lim=y_min_lim,
                                               x_max_lim=x_max_lim,
                                               y_max_lim=y_max_lim,
                                               yaxislabel="Dispersion",
                                               xticks_template=xticks,
                                               set_descriptions=set_descriptions
                                               )
        sets = []
        for i,this_set in enumerate(all_sets):
            sets.append( agr_singleset_template.substitute(set_number = i,
                                                           xydata = this_set)
                         )
        the_sets = "&\n".join(sets)
        
        s = agr_template.substitute(graphs=graphs,sets=the_sets)
        
        return s,None
        
        
agr_template = Template(
"""
# Grace project file
#
@version 50122
@page size 792, 612
@page scroll 5%
@page inout 5%
@link page off
@map font 8 to "Courier", "Courier"
@map font 10 to "Courier-Bold", "Courier-Bold"
@map font 11 to "Courier-BoldOblique", "Courier-BoldOblique"
@map font 9 to "Courier-Oblique", "Courier-Oblique"
@map font 4 to "Helvetica", "Helvetica"
@map font 6 to "Helvetica-Bold", "Helvetica-Bold"
@map font 7 to "Helvetica-BoldOblique", "Helvetica-BoldOblique"
@map font 5 to "Helvetica-Oblique", "Helvetica-Oblique"
@map font 14 to "NimbusMonoL-BoldOblique", "NimbusMonoL-BoldOblique"
@map font 15 to "NimbusMonoL-Regular", "NimbusMonoL-Regular"
@map font 16 to "NimbusMonoL-RegularOblique", "NimbusMonoL-RegularOblique"
@map font 17 to "NimbusRomanNo9L-Medium", "NimbusRomanNo9L-Medium"
@map font 18 to "NimbusRomanNo9L-MediumItalic", "NimbusRomanNo9L-MediumItalic"
@map font 19 to "NimbusRomanNo9L-Regular", "NimbusRomanNo9L-Regular"
@map font 20 to "NimbusRomanNo9L-RegularItalic", "NimbusRomanNo9L-RegularItalic"
@map font 21 to "NimbusSansL-Bold", "NimbusSansL-Bold"
@map font 22 to "NimbusSansL-BoldCondensed", "NimbusSansL-BoldCondensed"
@map font 23 to "NimbusSansL-BoldCondensedItalic", "NimbusSansL-BoldCondensedItalic"
@map font 24 to "NimbusSansL-BoldItalic", "NimbusSansL-BoldItalic"
@map font 25 to "NimbusSansL-Regular", "NimbusSansL-Regular"
@map font 26 to "NimbusSansL-RegularCondensed", "NimbusSansL-RegularCondensed"
@map font 27 to "NimbusSansL-RegularCondensedItalic", "NimbusSansL-RegularCondensedItalic"
@map font 28 to "NimbusSansL-RegularItalic", "NimbusSansL-RegularItalic"
@map font 29 to "StandardSymbolsL-Regular", "StandardSymbolsL-Regular"
@map font 12 to "Symbol", "Symbol"
@map font 31 to "Symbol-Regular", "Symbol-Regular"
@map font 2 to "Times-Bold", "Times-Bold"
@map font 3 to "Times-BoldItalic", "Times-BoldItalic"
@map font 1 to "Times-Italic", "Times-Italic"
@map font 0 to "Times-Roman", "Times-Roman"
@map font 36 to "URWBookmanL-DemiBold", "URWBookmanL-DemiBold"
@map font 37 to "URWBookmanL-DemiBoldItalic", "URWBookmanL-DemiBoldItalic"
@map font 38 to "URWBookmanL-Light", "URWBookmanL-Light"
@map font 39 to "URWBookmanL-LightItalic", "URWBookmanL-LightItalic"
@map font 40 to "URWChanceryL-MediumItalic", "URWChanceryL-MediumItalic"
@map font 41 to "URWGothicL-Book", "URWGothicL-Book"
@map font 42 to "URWGothicL-BookOblique", "URWGothicL-BookOblique"
@map font 43 to "URWGothicL-Demi", "URWGothicL-Demi"
@map font 44 to "URWGothicL-DemiOblique", "URWGothicL-DemiOblique"
@map font 45 to "URWPalladioL-Bold", "URWPalladioL-Bold"
@map font 46 to "URWPalladioL-BoldItalic", "URWPalladioL-BoldItalic"
@map font 47 to "URWPalladioL-Italic", "URWPalladioL-Italic"
@map font 48 to "URWPalladioL-Roman", "URWPalladioL-Roman"
@map font 13 to "ZapfDingbats", "ZapfDingbats"
@map color 0 to (255, 255, 255), "white"
@map color 1 to (0, 0, 0), "black"
@map color 2 to (255, 0, 0), "red"
@map color 3 to (0, 255, 0), "green"
@map color 4 to (0, 0, 255), "blue"
@map color 5 to (255, 255, 0), "yellow"
@map color 6 to (188, 143, 143), "brown"
@map color 7 to (220, 220, 220), "grey"
@map color 8 to (148, 0, 211), "violet"
@map color 9 to (0, 255, 255), "cyan"
@map color 10 to (255, 0, 255), "magenta"
@map color 11 to (255, 165, 0), "orange"
@map color 12 to (114, 33, 188), "indigo"
@map color 13 to (103, 7, 72), "maroon"
@map color 14 to (64, 224, 208), "turquoise"
@map color 15 to (0, 139, 0), "green4"
@reference date 0
@date wrap off
@date wrap year 1950
@default linewidth 1.0
@default linestyle 1
@default color 1
@default pattern 1
@default font 0
@default char size 1.000000
@default symbol size 1.000000
@default sformat "%.8g"
@background color 0
@page background fill on
@timestamp off
@timestamp 0.03, 0.03
@timestamp color 1
@timestamp rot 0
@timestamp font 0
@timestamp char size 1.000000
@timestamp def "Wed Jul 30 16:44:34 2014"
@r0 off
@link r0 to g0
@r0 type above
@r0 linestyle 1
@r0 linewidth 1.0
@r0 color 1
@r0 line 0, 0, 0, 0
@r1 off
@link r1 to g0
@r1 type above
@r1 linestyle 1
@r1 linewidth 1.0
@r1 color 1
@r1 line 0, 0, 0, 0
@r2 off
@link r2 to g0
@r2 type above
@r2 linestyle 1
@r2 linewidth 1.0
@r2 color 1
@r2 line 0, 0, 0, 0
@r3 off
@link r3 to g0
@r3 type above
@r3 linestyle 1
@r3 linewidth 1.0
@r3 color 1
@r3 line 0, 0, 0, 0
@r4 off
@link r4 to g0
@r4 type above
@r4 linestyle 1
@r4 linewidth 1.0
@r4 color 1
@r4 line 0, 0, 0, 0
$graphs
$sets
"""
)

agr_xticks_template = Template(
"""
@    xaxis  tick spec $num_labels
$single_xtick_templates
""")

agr_single_xtick_template = Template(
"""
@    xaxis  tick major $index, $coord
@    xaxis  ticklabel $index, "$name"
""")

agr_graph_template = Template(
"""
@g0 on
@g0 hidden false
@g0 type XY
@g0 stacked false
@g0 bar hgap 0.000000
@g0 fixedpoint off
@g0 fixedpoint type 0
@g0 fixedpoint xy 0.000000, 0.000000
@g0 fixedpoint format general general
@g0 fixedpoint prec 6, 6
@with g0
@    world $x_min_lim, $y_min_lim, $x_max_lim, $y_max_lim
@    stack world 0, 0, 0, 0
@    znorm 1
@    view 0.150000, 0.150000, 1.150000, 0.850000
@    title ""
@    title font 0
@    title size 1.500000
@    title color 1
@    subtitle ""
@    subtitle font 0
@    subtitle size 1.000000
@    subtitle color 1
@    xaxes scale Normal
@    yaxes scale Normal
@    xaxes invert off
@    yaxes invert off
@    xaxis  on
@    xaxis  type zero false
@    xaxis  offset 0.000000 , 0.000000
@    xaxis  bar on
@    xaxis  bar color 1
@    xaxis  bar linestyle 1
@    xaxis  bar linewidth 1.0
@    xaxis  label ""
@    xaxis  label layout para
@    xaxis  label place auto
@    xaxis  label char size 1.000000
@    xaxis  label font 4
@    xaxis  label color 1
@    xaxis  label place normal
@    xaxis  tick on
@    xaxis  tick major 5
@    xaxis  tick minor ticks 0
@    xaxis  tick default 6
@    xaxis  tick place rounded true
@    xaxis  tick in
@    xaxis  tick major size 1.000000
@    xaxis  tick major color 1
@    xaxis  tick major linewidth 1.0
@    xaxis  tick major linestyle 1
@    xaxis  tick major grid on
@    xaxis  tick minor color 1
@    xaxis  tick minor linewidth 1.0
@    xaxis  tick minor linestyle 1
@    xaxis  tick minor grid off
@    xaxis  tick minor size 0.500000
@    xaxis  ticklabel on
@    xaxis  ticklabel format general
@    xaxis  ticklabel prec 5
@    xaxis  ticklabel formula ""
@    xaxis  ticklabel append ""
@    xaxis  ticklabel prepend ""
@    xaxis  ticklabel angle 0
@    xaxis  ticklabel skip 0
@    xaxis  ticklabel stagger 0
@    xaxis  ticklabel place normal
@    xaxis  ticklabel offset auto
@    xaxis  ticklabel offset 0.000000 , 0.010000
@    xaxis  ticklabel start type auto
@    xaxis  ticklabel start 0.000000
@    xaxis  ticklabel stop type auto
@    xaxis  ticklabel stop 0.000000
@    xaxis  ticklabel char size 1.500000
@    xaxis  ticklabel font 4
@    xaxis  ticklabel color 1
@    xaxis  tick place both
@    xaxis  tick spec type both
$xticks_template
@    yaxis  on
@    yaxis  type zero false
@    yaxis  offset 0.000000 , 0.000000
@    yaxis  bar on
@    yaxis  bar color 1
@    yaxis  bar linestyle 1
@    yaxis  bar linewidth 1.0
@    yaxis  label "$yaxislabel"
@    yaxis  label layout para
@    yaxis  label place auto
@    yaxis  label char size 1.500000
@    yaxis  label font 4
@    yaxis  label color 1
@    yaxis  label place normal
@    yaxis  tick on
@    yaxis  tick major 0.2
@    yaxis  tick minor ticks 3
@    yaxis  tick default 6
@    yaxis  tick place rounded true
@    yaxis  tick in
@    yaxis  tick major size 1.000000
@    yaxis  tick major color 1
@    yaxis  tick major linewidth 1.0
@    yaxis  tick major linestyle 1
@    yaxis  tick major grid off
@    yaxis  tick minor color 1
@    yaxis  tick minor linewidth 1.0
@    yaxis  tick minor linestyle 1
@    yaxis  tick minor grid off
@    yaxis  tick minor size 0.500000
@    yaxis  ticklabel on
@    yaxis  ticklabel format general
@    yaxis  ticklabel prec 5
@    yaxis  ticklabel formula ""
@    yaxis  ticklabel append ""
@    yaxis  ticklabel prepend ""
@    yaxis  ticklabel angle 0
@    yaxis  ticklabel skip 0
@    yaxis  ticklabel stagger 0
@    yaxis  ticklabel place normal
@    yaxis  ticklabel offset auto
@    yaxis  ticklabel offset 0.000000 , 0.010000
@    yaxis  ticklabel start type auto
@    yaxis  ticklabel start 0.000000
@    yaxis  ticklabel stop type auto
@    yaxis  ticklabel stop 0.000000
@    yaxis  ticklabel char size 1.250000
@    yaxis  ticklabel font 4
@    yaxis  ticklabel color 1
@    yaxis  tick place both
@    yaxis  tick spec type none
@    altxaxis  off
@    altyaxis  off
@    legend on
@    legend loctype view
@    legend 0.85, 0.8
@    legend box color 1
@    legend box pattern 1
@    legend box linewidth 1.0
@    legend box linestyle 1
@    legend box fill color 0
@    legend box fill pattern 1
@    legend font 0
@    legend char size 1.000000
@    legend color 1
@    legend length 4
@    legend vgap 1
@    legend hgap 1
@    legend invert false
@    frame type 0
@    frame linestyle 1
@    frame linewidth 1.0
@    frame color 1
@    frame pattern 1
@    frame background color 0
@    frame background pattern 0
$set_descriptions
"""
)

agr_set_description_template = Template(
"""
@    s$set_number hidden false
@    s$set_number type xy
@    s$set_number symbol 0
@    s$set_number symbol size 1.000000
@    s$set_number symbol color 1
@    s$set_number symbol pattern 1
@    s$set_number symbol fill color 1
@    s$set_number symbol fill pattern 0
@    s$set_number symbol linewidth 1.0
@    s$set_number symbol linestyle 1
@    s$set_number symbol char 65
@    s$set_number symbol char font 0
@    s$set_number symbol skip 0
@    s$set_number line type 1
@    s$set_number line linestyle 1
@    s$set_number line linewidth $linewidth
@    s$set_number line color 1
@    s$set_number line pattern 1
@    s$set_number baseline type 0
@    s$set_number baseline off
@    s$set_number dropline off
@    s$set_number fill type 0
@    s$set_number fill rule 0
@    s$set_number fill color 1
@    s$set_number fill pattern 1
@    s$set_number avalue off
@    s$set_number avalue type 2
@    s$set_number avalue char size 1.000000
@    s$set_number avalue font 0
@    s$set_number avalue color 1
@    s$set_number avalue rot 0
@    s$set_number avalue format general
@    s$set_number avalue prec 3
@    s$set_number avalue prepend ""
@    s$set_number avalue append ""
@    s$set_number avalue offset 0.000000 , 0.000000
@    s$set_number errorbar on
@    s$set_number errorbar place both
@    s$set_number errorbar color 1
@    s$set_number errorbar pattern 1
@    s$set_number errorbar size 1.000000
@    s$set_number errorbar linewidth 1.0
@    s$set_number errorbar linestyle 1
@    s$set_number errorbar riser linewidth 1.0
@    s$set_number errorbar riser linestyle 1
@    s$set_number errorbar riser clip off
@    s$set_number errorbar riser clip length 0.100000
@    s$set_number comment "Cols 1:2"
@    s$set_number legend  ""
"""
)

agr_singleset_template = Template(
"""
@target G0.S$set_number
@type xy
$xydata
""")




        
