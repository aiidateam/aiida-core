# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This module defines the (physical) constants that are used throughout
the code. Note that 
"""


bohr_to_ang = 0.52917720859
ang_to_m = 1.e-10
bohr_si = bohr_to_ang * ang_to_m
ry_to_ev = 13.6056917253
ry_si = 4.35974394 / 2. * 10 ** (-18)
hartree_to_ev = ry_to_ev * 2.
timeau_to_sec = 2.418884326155573e-17
invcm_to_THz = 0.0299792458

# Element table, from NIST (http://www.nist.gov/pml/data/index.cfm)
# Retrieved in October 2014 for atomic numbers 1-103, and in May 2016
# for atomic numbers 104-112, 114 and 116.
elements = {
    1: {'mass': 1.00794, 'name': 'Hydrogen', 'symbol': 'H'},
    2: {'mass': 4.002602, 'name': 'Helium', 'symbol': 'He'},
    3: {'mass': 6.941, 'name': 'Lithium', 'symbol': 'Li'},
    4: {'mass': 9.012182, 'name': 'Beryllium', 'symbol': 'Be'},
    5: {'mass': 10.811, 'name': 'Boron', 'symbol': 'B'},
    6: {'mass': 12.0107, 'name': 'Carbon', 'symbol': 'C'},
    7: {'mass': 14.0067, 'name': 'Nitrogen', 'symbol': 'N'},
    8: {'mass': 15.9994, 'name': 'Oxygen', 'symbol': 'O'},
    9: {'mass': 18.9984032, 'name': 'Fluorine', 'symbol': 'F'},
    10: {'mass': 20.1797, 'name': 'Neon', 'symbol': 'Ne'},
    11: {'mass': 22.98977, 'name': 'Sodium', 'symbol': 'Na'},
    12: {'mass': 24.305, 'name': 'Magnesium', 'symbol': 'Mg'},
    13: {'mass': 26.981538, 'name': 'Aluminium', 'symbol': 'Al'},
    14: {'mass': 28.0855, 'name': 'Silicon', 'symbol': 'Si'},
    15: {'mass': 30.973761, 'name': 'Phosphorus', 'symbol': 'P'},
    16: {'mass': 32.065, 'name': 'Sulfur', 'symbol': 'S'},
    17: {'mass': 35.453, 'name': 'Chlorine', 'symbol': 'Cl'},
    18: {'mass': 39.948, 'name': 'Argon', 'symbol': 'Ar'},
    19: {'mass': 39.0983, 'name': 'Potassium', 'symbol': 'K'},
    20: {'mass': 40.078, 'name': 'Calcium', 'symbol': 'Ca'},
    21: {'mass': 44.955912, 'name': 'Scandium', 'symbol': 'Sc'},
    22: {'mass': 47.867, 'name': 'Titanium', 'symbol': 'Ti'},
    23: {'mass': 50.9415, 'name': 'Vanadium', 'symbol': 'V'},
    24: {'mass': 51.9961, 'name': 'Chromium', 'symbol': 'Cr'},
    25: {'mass': 54.938045, 'name': 'Manganese', 'symbol': 'Mn'},
    26: {'mass': 55.845, 'name': 'Iron', 'symbol': 'Fe'},
    27: {'mass': 58.933195, 'name': 'Cobalt', 'symbol': 'Co'},
    28: {'mass': 58.6934, 'name': 'Nickel', 'symbol': 'Ni'},
    29: {'mass': 63.546, 'name': 'Copper', 'symbol': 'Cu'},
    30: {'mass': 65.38, 'name': 'Zinc', 'symbol': 'Zn'},
    31: {'mass': 69.723, 'name': 'Gallium', 'symbol': 'Ga'},
    32: {'mass': 72.64, 'name': 'Germanium', 'symbol': 'Ge'},
    33: {'mass': 74.9216, 'name': 'Arsenic', 'symbol': 'As'},
    34: {'mass': 78.96, 'name': 'Selenium', 'symbol': 'Se'},
    35: {'mass': 79.904, 'name': 'Bromine', 'symbol': 'Br'},
    36: {'mass': 83.798, 'name': 'Krypton', 'symbol': 'Kr'},
    37: {'mass': 85.4678, 'name': 'Rubidium', 'symbol': 'Rb'},
    38: {'mass': 87.62, 'name': 'Strontium', 'symbol': 'Sr'},
    39: {'mass': 88.90585, 'name': 'Yttrium', 'symbol': 'Y'},
    40: {'mass': 91.224, 'name': 'Zirconium', 'symbol': 'Zr'},
    41: {'mass': 92.90638, 'name': 'Niobium', 'symbol': 'Nb'},
    42: {'mass': 95.96, 'name': 'Molybdenum', 'symbol': 'Mo'},
    43: {'mass': 98.0, 'name': 'Technetium', 'symbol': 'Tc'},
    44: {'mass': 101.07, 'name': 'Ruthenium', 'symbol': 'Ru'},
    45: {'mass': 102.9055, 'name': 'Rhodium', 'symbol': 'Rh'},
    46: {'mass': 106.42, 'name': 'Palladium', 'symbol': 'Pd'},
    47: {'mass': 107.8682, 'name': 'Silver', 'symbol': 'Ag'},
    48: {'mass': 112.411, 'name': 'Cadmium', 'symbol': 'Cd'},
    49: {'mass': 114.818, 'name': 'Indium', 'symbol': 'In'},
    50: {'mass': 118.71, 'name': 'Tin', 'symbol': 'Sn'},
    51: {'mass': 121.76, 'name': 'Antimony', 'symbol': 'Sb'},
    52: {'mass': 127.6, 'name': 'Tellurium', 'symbol': 'Te'},
    53: {'mass': 126.90447, 'name': 'Iodine', 'symbol': 'I'},
    54: {'mass': 131.293, 'name': 'Xenon', 'symbol': 'Xe'},
    55: {'mass': 132.9054519, 'name': 'Caesium', 'symbol': 'Cs'},
    56: {'mass': 137.327, 'name': 'Barium', 'symbol': 'Ba'},
    57: {'mass': 138.90547, 'name': 'Lanthanum', 'symbol': 'La'},
    58: {'mass': 140.116, 'name': 'Cerium', 'symbol': 'Ce'},
    59: {'mass': 140.90765, 'name': 'Praseodymium', 'symbol': 'Pr'},
    60: {'mass': 144.242, 'name': 'Neodymium', 'symbol': 'Nd'},
    61: {'mass': 145.0, 'name': 'Promethium', 'symbol': 'Pm'},
    62: {'mass': 150.36, 'name': 'Samarium', 'symbol': 'Sm'},
    63: {'mass': 151.964, 'name': 'Europium', 'symbol': 'Eu'},
    64: {'mass': 157.25, 'name': 'Gadolinium', 'symbol': 'Gd'},
    65: {'mass': 158.92535, 'name': 'Terbium', 'symbol': 'Tb'},
    66: {'mass': 162.5, 'name': 'Dysprosium', 'symbol': 'Dy'},
    67: {'mass': 164.93032, 'name': 'Holmium', 'symbol': 'Ho'},
    68: {'mass': 167.259, 'name': 'Erbium', 'symbol': 'Er'},
    69: {'mass': 168.93421, 'name': 'Thulium', 'symbol': 'Tm'},
    70: {'mass': 173.054, 'name': 'Ytterbium', 'symbol': 'Yb'},
    71: {'mass': 174.9668, 'name': 'Lutetium', 'symbol': 'Lu'},
    72: {'mass': 178.49, 'name': 'Hafnium', 'symbol': 'Hf'},
    73: {'mass': 180.94788, 'name': 'Tantalum', 'symbol': 'Ta'},
    74: {'mass': 183.84, 'name': 'Tungsten', 'symbol': 'W'},
    75: {'mass': 186.207, 'name': 'Rhenium', 'symbol': 'Re'},
    76: {'mass': 190.23, 'name': 'Osmium', 'symbol': 'Os'},
    77: {'mass': 192.217, 'name': 'Iridium', 'symbol': 'Ir'},
    78: {'mass': 195.084, 'name': 'Platinum', 'symbol': 'Pt'},
    79: {'mass': 196.966569, 'name': 'Gold', 'symbol': 'Au'},
    80: {'mass': 200.59, 'name': 'Mercury', 'symbol': 'Hg'},
    81: {'mass': 204.3833, 'name': 'Thallium', 'symbol': 'Tl'},
    82: {'mass': 207.2, 'name': 'Lead', 'symbol': 'Pb'},
    83: {'mass': 208.9804, 'name': 'Bismuth', 'symbol': 'Bi'},
    84: {'mass': 209.0, 'name': 'Polonium', 'symbol': 'Po'},
    85: {'mass': 210.0, 'name': 'Astatine', 'symbol': 'At'},
    86: {'mass': 222.0, 'name': 'Radon', 'symbol': 'Rn'},
    87: {'mass': 223.0, 'name': 'Francium', 'symbol': 'Fr'},
    88: {'mass': 226.0, 'name': 'Radium', 'symbol': 'Ra'},
    89: {'mass': 227.0, 'name': 'Actinium', 'symbol': 'Ac'},
    90: {'mass': 232.03806, 'name': 'Thorium', 'symbol': 'Th'},
    91: {'mass': 231.03588, 'name': 'Protactinium', 'symbol': 'Pa'},
    92: {'mass': 238.02891, 'name': 'Uranium', 'symbol': 'U'},
    93: {'mass': 237.0, 'name': 'Neptunium', 'symbol': 'Np'},
    94: {'mass': 244.0, 'name': 'Plutonium', 'symbol': 'Pu'},
    95: {'mass': 243.0, 'name': 'Americium', 'symbol': 'Am'},
    96: {'mass': 247.0, 'name': 'Curium', 'symbol': 'Cm'},
    97: {'mass': 247.0, 'name': 'Berkelium', 'symbol': 'Bk'},
    98: {'mass': 251.0, 'name': 'Californium', 'symbol': 'Cf'},
    99: {'mass': 252.0, 'name': 'Einsteinium', 'symbol': 'Es'},
    100: {'mass': 257.0, 'name': 'Fermium', 'symbol': 'Fm'},
    101: {'mass': 258.0, 'name': 'Mendelevium', 'symbol': 'Md'},
    102: {'mass': 259.0, 'name': 'Nobelium', 'symbol': 'No'},
    103: {'mass': 262.0, 'name': 'Lawrencium', 'symbol': 'Lr'},
    104: {'mass': 267.0, 'name': 'Rutherfordium', 'symbol': 'Rf'},
    105: {'mass': 268.0, 'name': 'Dubnium', 'symbol': 'Db'},
    106: {'mass': 271.0, 'name': 'Seaborgium', 'symbol': 'Sg'},
    107: {'mass': 272.0, 'name': 'Bohrium', 'symbol': 'Bh'},
    108: {'mass': 270.0, 'name': 'Hassium', 'symbol': 'Hs'},
    109: {'mass': 276.0, 'name': 'Meitnerium', 'symbol': 'Mt'},
    110: {'mass': 281.0, 'name': 'Darmstadtium', 'symbol': 'Ds'},
    111: {'mass': 280.0, 'name': 'Roentgenium', 'symbol': 'Rg'},
    112: {'mass': 285.0, 'name': 'Copernicium', 'symbol': 'Cn'},
    114: {'mass': 289.0, 'name': 'Flerovium', 'symbol': 'Fl'},
    116: {'mass': 293.0, 'name': 'Livermorium', 'symbol': 'Lv'},
}
