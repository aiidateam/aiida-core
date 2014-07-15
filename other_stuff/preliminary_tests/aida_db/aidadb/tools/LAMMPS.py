#!/usr/bin/python
import ase.io
import ase
from ase import units
from ase.data import s22
from ase.calculators.lammps import LAMMPS
from multiasecalc.lammps.reaxff import ReaxFF
from multiasecalc.lammps.compass import COMPASS
from multiasecalc.lammps.dynamics import LAMMPSOptimizer, LAMMPS_NVT
from multiasecalc.utils import get_datafile
import sys

def printenergy(a):
    epot = a.get_potential_energy() / len(a)
    ekin = a.get_kinetic_energy() / len(a)
    print ("Energy per atom: Epot = %.3feV  Ekin = %.3feV (T=%3.0fK)  Etot = %.3feV" %
           (epot, ekin, ekin/(1.5*units.kB), epot+ekin))

def runMD(atoms, steps):

  MaxwellBoltzmannDistribution(atoms, 3*units.kB)
  dyn = VelocityVerlet(atoms, 5*units.fs)  # 5 fs time step.

  for i in range(steps):
    dyn.run(10)
    printenergy(atoms)


def getStress(c):

  calc = LAMMPS()
  c.set_calculator(calc)
  return c.get_stress()

def runMD(c, steps):

  calc = LAMMPS()
  c.set_calculator(calc)

  MaxwellBoltzmannDistribution(atoms, 3*units.kB)
  dyn = VelocityVerlet(atoms, 5*units.fs)  # 5 fs time step.

  for i in range(steps):
    dyn.run(10)
    #printenergy(atoms)

  return c

