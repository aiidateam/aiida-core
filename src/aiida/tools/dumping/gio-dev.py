# Implementation for now, could be eventually method of the class, or export functionality via e.g. entry point `aiida.core.exports.export_structure` -> Needs to be discoverable
def export_structure(node, folder, **kargs): # GP: support both functions and class methods => in the signature, the first has to be the node
    pass # GP: dump what you have to dump in the folder, e.g. xsf or cif

plugin_mapping = {
    'core.structure': export_structure,
    'upf': None,
    'core.bands':
}

# check in the CLI what exporters we have

verdi group dump --also-rich=yes --rich-options-config=conf.txt --rich-options=....

# Different ways how one could define the syntax via the CLI (mirror similar behavior in )
core.structure:
core.structure:aiida.core.exports.export_structure
core.structure:aiida.core.exports.export_structure:format=xsf
type=core.structure:export=aiida.core.exports.export_structure:format=xsf

core.structure::format=xsf

core.structure:null

# GP: Not specified means use the default, for now from hardcoded list, in the future reading from some defined method of the plugin

# This could be entry point given in plugin
aiida.orm.data.StructureData.export_to_dir # think to a syntax for methods