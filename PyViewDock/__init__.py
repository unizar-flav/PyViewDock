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

  - Align a single structure to every state of an existing multi-state object:
        align_multi  mobile, target [, name_new [, initial_state [, final_state [, source_state ]]]]


  github.com/unizar-flav/PyViewDock
  by Sergio Boneta Martinez
  GPLv3 2021-2023

"""

__version__ = '0.3.4'

from pymol import cmd, plugins

from . import gui, io, misc


##  PYMOL FUNCTIONS  ##################################################
cmd.extend("load_dock4", io.load_dock4)
cmd.extend("load_pydock", io.load_pydock)
cmd.extend("load_xyz", io.load_xyz)
cmd.extend("export_docked_data", io.export_docked_data)
cmd.extend("align_multi", misc.align_multi)
# Override built-in functions -----------------------------------------
cmd.load = io.load_ext
cmd.extend("load", cmd.load)
cmd.set_name = misc.set_name_catcher
cmd.extend("set_name", cmd.set_name)

##  GUI  ##############################################################
def __init_plugin__(app=None):
    """Add an entry to the PyMOL 'Plugin' menu"""
    plugins.addmenuitemqt("PyViewDock", gui.run_gui)
