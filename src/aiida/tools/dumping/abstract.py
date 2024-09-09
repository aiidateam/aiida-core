# TODO: The output path creation could be put here, bc I need this time and time again.
# Could add saveguard file with filename based on class name or sthg like that
#

class AbstractDumper():
    def __init__(self, overwrite, incremental):
        self.overwrite = overwrite
        self.incremental = incremental


