# PyViewDock

*ViewDock plug-in for PyMOL*

![PyMOL](https://img.shields.io/badge/PyMOL-2.x-green.svg)
![python](https://img.shields.io/badge/python->3.6-red.svg)

A [PyMOL](https://pymolwiki.org) plug-in that adds capabilities to this molecular viewer to manage result files from docking. Currently tested for [Swiss-Dock](http://www.swissdock.ch/). \
Obviously inspired from the original [Chimera's View-Dock](https://www.cgl.ucsf.edu/chimera/docs/ContributedSoftware/viewdock/framevd.html)


### Requirements

PyMOL 2.x with PyQt5

For [open-source PyMOL](https://github.com/schrodinger/pymol-open-source), ensure having PyQt5 by `python -m pip install pyqt5 --user`


### Installation

It can be easily installed through the PyMOL's [plugin manager](https://pymolwiki.org/index.php/Plugin_Manager): `Plugin > Plugin Manager > Install New Plugin`

A [downloaded zip](https://github.com/unizar-qtc/PyViewDock/archive/master.zip) file of this plug-in can be choosen or directly provide the repository URL: `https://github.com/unizar-qtc/PyViewDock/archive/master.zip`


### Usage

#### Command line

  - Load a .chimerax file: \
      `load  filename`

  - Load cluster of docked ligands in PDB format: \
      `load_cluster  filename [, object [, mode ]]`

#### GUI

Initialize the plug-in window in `Plugin > PyViewDock`.\
Open a PDB file with docked ligands through `File > Open...`.

A table will appear with information extracted from the *REMARK* section of the PDB. It can be column-sorted, show/hide columns and an entry will be displayed on PyMOL when clicked.
