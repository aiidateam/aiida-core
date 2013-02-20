"""
To implement pseudopotentials in the upf format.

files = [the_upf_file] # Only one file allowed for the moment
jsons = {
   'upf_info': {dict with the parameters as element, functional, ...}
   }

properties (the compulsory ones):
* element
* functional
* pseudo_type (paw, rrkjus, ...)
methods:
* get_upf_path() # Return file path
* get_upf_url()  # Return aidaurl
* parse_content()# At some point we will probably implement a parser to
                   automatically fill the element, functional, ... fields
"""
