#!/usr/bin/env python3

"""
  PyViewDock: PyMOL plug-in to resemble ViewDock
  ==============================================

  Add extended capabilities to the PyMOL molecular
  viewer to manage docking result files


  - Load a .chimerax file:
        load  filename

  - Load cluster of docking ligands in PDB format:
        load_cluster  filename [, object [, mode ]]


  Remark: Currently tested only for Swiss-Dock


  by Sergio Boneta Martinez
  GPLv3 2021

"""

__version__ = '0.1.1'


from pymol import cmd, plugins

from .io import load_dock4, load_ext
from .gui import run_gui


##  PYMOL FUNCTIONS  ##################################################

cmd.extend("load_cluster", load_dock4)
cmd.load = load_ext
cmd.extend("load", cmd.load)


##  GUI  ##############################################################

def __init_plugin__(app=None):
    """Add an entry to the PyMOL 'Plugin' menu"""
    plugins.addmenuitemqt("PyViewDock", run_gui)
