# TODO: Use singledispatch to adapt functionality of method based on the type
# Derived data types from

class DataDumper:
    def __init__(self, node) -> None:
        self.node = node

    def generate_output_name(self):
        pass

    def dump(self):
        pass

    def _dump_structuredata(self):
        # ? There also exists a CifData file type
        pass

    def _dump_code(self):
        pass

    def _dump_computer(self):
        pass
