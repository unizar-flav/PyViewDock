#!/usr/bin/env python3

"""
  PyViewDock: PyMOL plug-in to resemble ViewDock
  ==============================================

  Add extended capabilities to the PyMOL molecular
  viewer to manage docking result files


  Enriched built-in 'load' function (also as drag-and-drop):
      * SwissDock's .chimerax
      * pyDock's .ene/.eneRST

  - Load cluster of docking ligands in Dock 4+ PDB format:
        load_dock4  filename [, object [, mode ]]

  - Load pyDock's .ene/.eneRST file:
        load_pydock  filename [, object [, max_n ]]

  - Load .xyz file (generic):
        load_xyz  filename [, object ]

  - Export docked entries data to .csv/.txt file:
        export_docked_data  filename [, format ]



  by Sergio Boneta Martinez
  GPLv3 2022

"""

__version__ = '0.2.6'


from pymol import cmd, plugins

from .io import load_dock4, load_pydock, load_xyz, load_ext, export_docked_data
from .gui import run_gui


##  PYMOL FUNCTIONS  ##################################################

cmd.extend("load_dock4", load_dock4)
cmd.extend("load_pydock", load_pydock)
cmd.extend("load_xyz", load_xyz)
cmd.extend("export_docked_data", export_docked_data)
cmd.load = load_ext
cmd.extend("load", cmd.load)


##  GUI  ##############################################################

def __init_plugin__(app=None):
    """Add an entry to the PyMOL 'Plugin' menu"""
    plugins.addmenuitemqt("PyViewDock", run_gui)
