# PyViewDock


[![PyMOL](https://img.shields.io/badge/PyMOL-2.x-green.svg)](https://pymolwiki.org)
[![python](https://img.shields.io/badge/python-3.6+-red.svg)](https://www.python.org/)

A [PyMOL](https://pymolwiki.org) plug-in that adds capabilities to this molecular viewer to manage result files from docking. \
Obviously inspired from the original [Chimera's View-Dock](https://www.cgl.ucsf.edu/chimera/docs/ContributedSoftware/viewdock/framevd.html)


### Supported formats with software/server results

* [Swiss-Dock](http://www.swissdock.ch/) \
    .chimerax / .pdb in Dock 4+ format


### Requirements

PyMOL 2.x with PyQt5

For [inventive PyMOL](https://pymol.org/2/) PyQt5 is already included.\
In the case of [open-source PyMOL](https://github.com/schrodinger/pymol-open-source), ensure to have PyQt5: `python -m pip install pyqt5 --user`


### Installation

Easy intallable. Open PyMOL and use it's [plugin manager](https://pymolwiki.org/index.php/Plugin_Manager): `Plugin > Plugin Manager > Install New Plugin`

You can [download a zip](https://github.com/unizar-qtc/PyViewDock/archive/master.zip) to install it from a local file or directly provide it an URL:

```
https://github.com/unizar-qtc/PyViewDock/archive/master.zip
```


### Usage

#### GUI

Toggle the plug-in window in `Plugin > PyViewDock`\
Open a PDB file with docked ligands through `File > Open...`

A table will appear with information for every docking entry. It can be column-sorted, show/hide columns and each entry will be displayed at PyMOL when clicked.

#### PyMOL command line

  - Load a .chimerax file (drag-and-drop also works): \
      `load  filename`

  - Load cluster of docked ligands in PDB format (Dock 4+): \
      `load_dock4  filename [, object [, mode ]]`
