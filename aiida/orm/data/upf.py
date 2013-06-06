"""
This module manages the UPF pseudopotentials in the local repository.
"""
from aiida.orm.data.singlefile import SinglefileData

class UpfData(SinglefileData): 
    
    @classmethod
    def get_or_create(cls,filename,element,pot_type,use_first = False):
        """
        Pass the same parameter of the init; if a file with the same md5
        is found, that UpfData is returned. 
        
        Args:
            filename: an absolute filename on disk
            element: the element this pseudopotential refers to
            pot_type: the potential type (lda, pbesol, ...) of this pseudo
            use_first: if False (default), raise an exception if more than 
                one potential is found.
                If it is True, instead, use the first available pseudopotential.
        Return:
            (upf, created), where upf is the UpfData object, and create is either
            True if the object was created, or False if the object was retrieved
            from the DB.
        """
        import aiida.common.utils
        import os
        
        if not os.path.abspath(filename):
            raise ValueError("filename must be an absolute path")
        md5 = aiida.common.utils.md5_file(filename)
        pseudos = cls.from_md5(md5)
        if len(pseudos) == 0:
            instance = cls(filename=filename, element=element,pot_type=pot_type).store()
            return (instance, True)
        else:
            filtered_pseudos = []
            for p in pseudos:
                if (p.get_attr("element", None) == element and
                      p.get_attr("pot_type", None) == pot_type):
                    filtered_pseudos.append(p)
            if len(filtered_pseudos) == 0:
                raise ValueError("At least one UPF found with the same md5, "
                    "but the element or the pot_type are different. "
                    "pks={}".format(
                        ",".join([str(i.pk) for i in pseudos])))
            elif len(filtered_pseudos) > 1:
                if use_first:
                    return (filtered_pseudos[0], False)
                else:
                    raise ValueError("More than one copy of a pseudopotential "
                        "with the same MD5 has been found in the "
                        "DB. pks={}".format(
                          ",".join([str(i.pk) for i in filtered_pseudos])))
            else:        
                return (filtered_pseudos[0], False)

    @classmethod
    def from_md5(cls, md5):
        """
        Return a list of all UPF pseudopotentials that match a given MD5 hash.
        
        Note that the hash has to be stored in a _md5 attribute, otherwise
        the pseudo will not be found.
        """
        queryset = cls.query(attributes__key='_md5', attributes__tval=md5)
        return list(queryset)


    def __init__(self, **kwargs):
        import aiida.common.utils
        
        
        uuid = kwargs.pop('uuid', None)
        if uuid is not None:
            if kwargs:
                raise TypeError("You cannot pass other arguments if one of"
                                "the arguments is uuid")
            super(UpfData,self).__init__(uuid=uuid)
            return
        
        super(UpfData,self).__init__()
        
        try:
            filename = kwargs.pop("filename")
        except KeyError:
            raise TypeError("You have to specify the filename")
        try:
            element = kwargs.pop("element")
        except KeyError:
            raise TypeError("You have to specify the element to which this "
                            "pseudo refers to")
            
        try:
            pot_type = kwargs.pop("pot_type")
        except KeyError:
            raise TypeError("You have to specify the pot_type of this "
                            "pseudo (lda, pbe, ...)")
        
        self.add_path(filename)
        md5sum = aiida.common.utils.md5_file(self.get_file_abs_path())
        
        self.set_attr('element', str(element))
        self.set_attr('pot_type', str(pot_type))
        self.set_attr('md5', md5sum)

    def validate(self):
        from aiida.common.exceptions import ValidationError

        super(UpfData,self).validate()
        
        try:
            self.get_attr('element')
        except AttributeError:
            raise ValidationError("attribute 'element' not set.")

        try:
            self.get_attr('pot_type')
        except AttributeError:
            raise ValidationError("attribute 'pot_type' not set.")

        try:
            self.get_attr('md5')
        except AttributeError:
            raise ValidationError("attribute 'md5' not set.")

