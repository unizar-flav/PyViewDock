"""
  Input / Output of Structures
  ============================

  Functions
  ---------
    load_dock4
    load_chimerax
    load_pydock
    load_xyz
    export_docked_data
    load_ext

"""

import os
import re
import xml.etree.ElementTree as ET
from glob import glob
from textwrap import dedent
from urllib.error import HTTPError
from urllib.request import urlopen

from pymol import cmd, importing, CmdException

from . import misc
from .docked import Docked, get_docked


def load_pdbqt(filename, object='') -> None:
    '''
    DESCRIPTION

        "load_pdbqt" loads an AutoDock Vina's PDBQT file as an object
        with multiple ligand poses and docking information

    USAGE

        load_pdbqt  filename [, object ]

    ARGUMENTS

        filename = string: structures in PDBQT format (.pdbqt)

        object = string: name to be include the new object
                         if absent, taken from filename

    EXAMPLES

        load_pdbqt  docking_result.pdbqt
        load_pdbqt  docking_restul.pdbqt, docking_01

    SEE ALSO

        load, load_chimerax, load_dock4, load_pydock, load_xyz
    '''

    docked = get_docked()

    if not object:
        object = os.path.basename(filename).split('.')[0]
    object = misc.non_repeated_object(object)

    docked.load_pdbqt(filename, object)
    print(f" PyViewDock: \"{filename}\" loaded as \"{object}\"")

cmd.auto_arg[0]['load_pdbqt'] = [lambda: cmd.Shortcut(glob('*.pdbqt')), 'filename', ', ']
cmd.auto_arg[1]['load_pdbqt'] = [cmd.object_sc, 'object', '']

def load_dock4(filename, object='', mode=0) -> None:
    '''
    DESCRIPTION

        "load_dock4" loads a SwissDock's cluster of ligands as an object
        with multiple states and read the docking information

    USAGE

        load_dock4  filename [, object [, mode ]]

    ARGUMENTS

        filename = string: cluster of structures in PDB format

        object = string: name to be include the new object
                         if absent, taken from filename

        mode = 0/1/2:
            0 - all molecules to same object {default}
            1 - only first molecule of each cluster to object (ClusterRank==0)
            2 - all molecules to multiple objects according to clusters

    EXAMPLES

        load_dock4  cluster.dock4.pdb
        load_dock4  cluster.dock4, clusters
        load_dock4  cluster.dock4, clusters, 2

    SEE ALSO

        load, load_pdbqt, load_chimerax, load_pydock, load_xyz
    '''

    docked = get_docked()

    # check file and read as list of strings
    if not os.path.isfile(filename):
        raise CmdException(f"File \"{filename}\" not found.", "PyViewDock")
    else:
        with open(filename, "rt") as f:
            cluster = f.readlines()

    if not object:
        object = os.path.basename(filename).split('.')[0]
    object = misc.non_repeated_object(object)

    docked.load_dock4(cluster, object, mode)
    print(f" PyViewDock: \"{filename}\" loaded as \"{object}\"")

cmd.auto_arg[0]['load_dock4'] = [lambda: cmd.Shortcut(glob('*.pdb') + glob('*.dock4')), 'filename', ', ']
cmd.auto_arg[1]['load_dock4'] = [cmd.object_sc, 'object', ', ']

def load_chimerax(filename) -> None:
    '''
    DESCRIPTION

        "load_chimerax" loads a UCSF ChimeraX file written by SwissDock

    USAGE

        load_chimerax  filename

    ARGUMENTS

        filename = string: chimerax file (XML file with URL of target and ligands cluster)

    EXAMPLES

        load_chimerax  cluster.chimerax

    SEE ALSO

        load, load_pdbqt, load_dock4, load_pydock, load_xyz
    '''

    # UCSF Chimera Web Data Format
    # www.cgl.ucsf.edu/chimera/docs/ContributedSoftware/webdata/chimerax.html

    docked = get_docked()

    # default naming for new objects
    target_object = misc.non_repeated_object('target')
    clusters_object = misc.non_repeated_object('clusters')

    print(f" PyViewDock: Loading \"{filename}\"")

    # read ChimeraX file as XML
    try:
        chimerax_xml = ET.parse(filename).getroot()
        target_url = chimerax_xml.find('web_files').find('file').get('loc')
        commands = chimerax_xml.find('commands').find('py_cmd').text
        cluster_url = re.findall('"(http[^"]+pdb)"', commands)[0]
        target_filename = target_url.split('/')[-1]
        cluster_filename = cluster_url.split('/')[-1]
        if not all([target_url, cluster_url, target_filename, cluster_filename]): raise ValueError
    except FileNotFoundError:
        raise CmdException(f"Failed reading 'chimerax' file. File not found.", "PyViewDock")
    except:
        raise CmdException(f"Failed reading 'chimerax' file. Invalid format.", "PyViewDock")
    else:
        # fetch files from server
        try:
            target_pdb = urlopen(target_url).read().decode('utf-8')
            cluster_pdb = urlopen(cluster_url).readlines()
            cluster_pdb = [i.decode('utf-8') for i in cluster_pdb]
            cmd.read_pdbstr(target_pdb, target_object)
            docked.load_dock4(cluster_pdb, clusters_object, 0)
        except HTTPError:
            print(" PyViewDock: Failed reading 'chimerax' file. Bad server response. Calculation too old?")
            # find local files that match names in .chimerax directory
            chimerax_directory = os.path.dirname(os.path.realpath(filename))
            target_file = os.path.join(chimerax_directory, target_filename)
            cluster_file = os.path.join(chimerax_directory, cluster_filename)
            if os.path.isfile(target_file) and os.path.isfile(target_file):
                print(f" PyViewDock: Files found locally ({target_filename}, {cluster_filename}). Loading...")
                importing.load(target_file, target_object)
                load_dock4(cluster_file, clusters_object, 0)

cmd.auto_arg[0]['load_chimerax'] = [lambda: cmd.Shortcut(glob('*.chimerax')), 'filename', '']

def load_pydock(filename, object='', max_n=100) -> None:
    '''
    DESCRIPTION

        "load_pydock" loads a PyDock's group of structures as an object
        with multiple states and read the docking information

    USAGE

        load_pydock  filename [, object [, max_n ]]

    ARGUMENTS

        filename = string: energy resume file (.ene / .eneRST)

        object = string: basename to include the new objects (_rec / _lig)
                         if absent, taken from filename

        max_n = integer: maximum number of structures to load {default: 100}

    EXAMPLES

        load_pydock  dock.ene
        load_pydock  dock.eneRST
        load_pydock  dock.eneRST, docked, 100

    SEE ALSO

        load, load_pdbqt, load_chimerax, load_dock4, load_xyz
    '''

    docked = get_docked()

    if not object:
        object = os.path.basename(filename).split('.')[0]

    docked.load_pydock(filename, object, max_n)
    print(f" PyViewDock: \"{filename}\" loaded as \"{object}\"")

cmd.auto_arg[0]['load_pydock'] = [lambda: cmd.Shortcut(glob('*.ene') + glob('*.eneRST')), 'filename', ', ']
cmd.auto_arg[1]['load_pydock'] = [cmd.object_sc, 'object', ', ']

def load_xyz(filename, object='') -> None:
    '''
    DESCRIPTION

        "load_xyz" loads a group of structures as an object from .xyz
        with multiple states and docking information

    USAGE

        load_xyz  filename [, object ]

    ARGUMENTS

        filename = string: coordinates file (.xyz)

        object = string: name to be include the new object
                         if absent, taken from filename

    EXAMPLES

        load_xyz  dock.xyz
        load_xyz  dock.xyz, docked

    SEE ALSO

        load, load_pdbqt, load_chimerax, load_dock4, load_pydock
    '''

    docked = get_docked()

    if not object:
        object = os.path.basename(filename).split('.')[0]
    object = misc.non_repeated_object(object)

    docked.load_xyz(filename, object)
    print(f" PyViewDock: \"{filename}\" loaded as \"{object}\"")

cmd.auto_arg[0]['load_xyz'] = [lambda: cmd.Shortcut(glob('*.xyz')), 'filename', ', ']
cmd.auto_arg[1]['load_xyz'] = [cmd.object_sc, 'object', '']

def export_docked_data(filename, format='') -> None:
    '''
    DESCRIPTION

        "export_docked_data" saves a file containing docked data of all entries

    USAGE

        export_docked_data  filename [, format ]

    ARGUMENTS

        filename = string: data output file

        format = string: file format, guessed from filename's suffix with fallback to default
                         csv : semicolon separated data {default}
                         txt : space separated data, with the header row preceded by '#'

    EXAMPLES

        export_docked_data  docked.csv
        export_docked_data  docked.txt
        export_docked_data  docked, txt
    '''

    docked = get_docked()

    if not format:
        suffix = os.path.basename(filename).rpartition('.')[-1].lower()
        format = suffix if suffix in {'csv', 'txt'} else 'csv'

    docked.export_data(filename, format)

cmd.auto_arg[0]['export_docked_data'] = [lambda: cmd.Shortcut(glob('*.csv') + glob('*.txt')), 'filename', ', ']
cmd.auto_arg[1]['export_docked_data'] = [lambda: cmd.Shortcut(['csv', 'txt']), 'format', '']

def load_ext(filename, object='', state=0, format='', finish=1,
             discrete=-1, quiet=1, multiplex=None, zoom=-1, partial=0,
             mimic=1, object_props=None, atom_props=None, *, _self=cmd):
    '''
    REMARK

        This is a wrapper by PyViewDock to the original "load" function
        with extended funtionality for docking file formats.

        .pdbqt
            PDBQT file with docking information from AutoDock Vina
        .dock4
            PDB Dock 4 format from SwissDock
        .chimerax
            XML file with URL of target and ligands cluster from SwissDock
        .ene / .eneRST
            energy table with reference numbers of structures from pyDock
    '''

    if not format:
        file_dot_separated = os.path.basename(filename).rpartition('.')
        object = object or "".join(file_dot_separated[:-2])
        format = file_dot_separated[-1]

    # Chimera X
    if format.lower() == "chimerax":
        load_chimerax(filename)

    # Dock 4
    elif format.lower() == "dock4":
        load_dock4(filename, object)

    # pyDock
    elif format.lower() in ("ene", "enerst"):
        load_pydock(filename, object)

    # PDBQT
    elif format.lower() == "pdbqt":
        load_pdbqt(filename, object)

    # original load function
    else:
        importing.load(filename, object, state, format, finish,
                        discrete, quiet, multiplex, zoom, partial)

load_ext.__doc__ = importing.load.__doc__ + dedent(load_ext.__doc__)
