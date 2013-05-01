"""
Implement subclass for a single file in the permanent repository
files = [one_single_file]
jsons = {}

methods:
* get_content
* get_path
* get_aidaurl (?)
* get_md5
* ...

To discuss: do we also need a simple directory class for full directories
in the perm repo?
"""
import os

from aida.orm import Data


class FileData(Data):
    """
    Pass as input either the uuid of an existing node, or a
    file parameter with the (absolute) path of a file on the hard drive.
    It will get copied inside.

    Internally must have a single file, and stores as internal attribute the filename
    in the '_filename' attribute.
    """
    _plugin_type_string = ".".join([Data._plugin_type_string,'file'])

    def __init__(self,filename=None,**kwargs):
        super(FileData,self).__init__(**kwargs)

        uuid = kwargs.pop('uuid', None)
        if uuid is not None:
            return

        if filename is not None:
            self.add_file(filename)

    def add_file(self,src_abs,dst_filename=None):
        """
        Add a single file
        """
        old_file_list = self.get_file_list()

        if dst_filename is None:
            final_filename = os.path.split(src_abs)[1]
        else:
            final_filename = dst_filename

        try:
            # I remove the 'filename' from the list of old files:
            # if I am overwriting the file, I don't want to delete if afterwards
            old_file_list.remove(dst_filename)
        except ValueError:
            # filename is not there: no problem, it simply means
            pass
            
        super(FileData,self).add_file(src_abs,final_filename)

        for delete_me in old_file_list:
            self.remove_file(delete_me)

        self.set_attr('filename', final_filename)

    def remove_file(self,filename):
        try:
            self.del_attr('filename', filename)
        except AttributeError:
            ## There was not file set
            pass

    def validate(self):
        from aida.common.exceptions import ValidationError

        super(FileData,self).validate()
        
        try:
            filename = self.get_attr('filename')
        except AttributeError:
            raise ValidationError("attribute 'filename' not set.")

        if [filename] != self.get_file_list():
            raise ValidationError("The list of files in the folder does not match the "
                                  "'filename' attribute. _filename='{}', files: {}".format(
                                      filename, self.get_file_list()))
        
    
