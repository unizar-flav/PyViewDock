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
import zipfile
from urllib.error import HTTPError
from urllib.request import urlopen

from pymol import cmd, importing, CmdException

from .docked import Docked, get_docked
from .misc import non_repeated_object


def load_dock4(filename, object='', mode=0) -> None:
    """
        Load a SwissDock's cluster of ligands as an object
        with multiple states and read the docking information

        Parameters
        ----------
        filename : str
            cluster of structures in PDB format
            or zip file containing a .dock4.pdb file
        object : str
            name to be include the new object
            if absent, taken from filename
        mode : {0, 1, 2}
            0 - all molecules to same object
            1 - only first molecule of each cluster to object
            2 - all molecules to multiple objects according to clusters
    """

    docked = get_docked()

    # check file and read as list of strings
    if not os.path.isfile(filename):
        raise CmdException(f"File \"{filename}\" not found.", "PyViewDock")
    elif zipfile.is_zipfile(filename):
        with zipfile.ZipFile(filename, 'r') as z:
            dock4_files = [i for i in z.namelist() if i.endswith('.dock4.pdb')]
            if not dock4_files:
                raise CmdException(f"No .dock4.pdb file found in \"{filename}\".", "PyViewDock")
            cluster = z.read(dock4_files[0]).decode('utf-8').split('\n')
    else:
        with open(filename, "rt") as f:
            cluster = f.readlines()

    if not object:
        object = os.path.basename(filename).split('.')[0]
    object = non_repeated_object(object)

    docked.load_dock4(cluster, object, mode)
    print(f" PyViewDock: \"{filename}\" loaded as \"{object}\"")

def load_chimerax(filename) -> None:
    """
        Load a UCSF ChimeraX file written by SwissDock

        Parameters
        ----------
        filename : str
            chimerax file (XML file with URL of target and ligands cluster)
    """

    # UCSF Chimera Web Data Format
    # www.cgl.ucsf.edu/chimera/docs/ContributedSoftware/webdata/chimerax.html

    docked = get_docked()

    # default naming for new objects
    target_object = non_repeated_object('target')
    clusters_object = non_repeated_object('clusters')

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

def load_pydock(filename, object='', max_n=100) -> None:
    """
        Load a PyDock's group of structures as an object
        with multiple states and read the docking information

        The energy resume file is read and the corresponding
        structures are taken from PDB files in the same folder
        based on the pattern NAME_NUMBER.pdb
        _rec.pdb and _lig.pdb are also necessary

        Parameters
        ----------
        filename : str
            energy resume file (.ene / .eneRST)
        object : str, optional
            basename to include the new objects (_rec / _lig)
            if absent, taken from filename
        max_n : int
            maximum number of structures to load
    """

    docked = get_docked()

    if not object:
        object = os.path.basename(filename).split('.')[0]
    object = non_repeated_object(object)

    docked.load_pydock(filename, object, max_n)
    print(f" PyViewDock: \"{filename}\" loaded as \"{object}\"")

def load_xyz(filename, object='') -> None:
    """
        Load a group of structures as an object from .xyz
        with multiple states and docking information

        Parameters
        ----------
        filename : str
            coordinates file (.xyz)
        object : str
            name to be include the new object
    """

    docked = get_docked()

    if not object:
        object = os.path.basename(filename).split('.')[0]
    object = non_repeated_object(object)

    docked.load_xyz(filename, object)
    print(f" PyViewDock: \"{filename}\" loaded as \"{object}\"")

def export_docked_data(filename, format='') -> None:
    """
        Save file containing docked data of all entries

        Parameters
        ----------
        filename : str
            data output file
        format : {'csv', 'txt'}, optional
            file format, default guessed from filename's suffix with fallback to 'csv'
            csv : semicolon separated data
            txt : space separated data, with the header row preceded by '#'
    """

    docked = get_docked()

    if not format:
        suffix = os.path.basename(filename).rpartition('.')[-1].lower()
        format = suffix if suffix in {'csv', 'txt'} else 'csv'

    docked.export_data(filename, format)

def load_ext(filename, object='', state=0, format='', finish=1,
             discrete=-1, quiet=1, multiplex=None, zoom=-1, partial=0,
             mimic=1, object_props=None, atom_props=None, *, _self=cmd):
    """
        Wrapper to load function with extended funtionality

        Formats
        -------
        .chimerax
            XML file with URL of target and ligands cluster
        .ene / .eneRST
            energy table with reference numbers of structures from pyDock
    """

    if not format:
        file_dot_separated = os.path.basename(filename).rpartition('.')
        name   = "".join(file_dot_separated[:-2])
        format = file_dot_separated[-1]

    # Chimera X
    if format.lower() == "chimerax":
        load_chimerax(filename)

    # pyDock
    elif format.lower() in ("ene", "enerst"):
        load_pydock(filename, name)

    # original load function
    else:
        importing.load(filename, object, state, format, finish,
                        discrete, quiet, multiplex, zoom, partial)
