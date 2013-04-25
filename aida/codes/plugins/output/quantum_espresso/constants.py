class QEConversionConstants(object):
    """
    Physical variables. Note that every code has its own conversion units
    that have to be used when converting the data in the default units
    eventually this class could be moved elsewhere
    """
    # TODO : add the constants for electrical quantities
    def __init__(self):
        self.bohr_to_ang=0.52917720859
        self.ang_to_m=1.e-10
        self.ry_to_ev=13.6056917253
        self.hartree_to_ev = self.ry_to_ev*2.
        self.timeau_to_sec = 2.418884326155573e-17
