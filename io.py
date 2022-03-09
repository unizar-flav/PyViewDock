"""
  Input / Output of Structures
  ============================

"""


import os
import re
import glob
from copy import deepcopy
import xml.etree.ElementTree as ET
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from pymol import cmd, importing, CmdException


##  DOCKED STRUCTURES CLASS  ##########################################

class Docked():

    """
        Group of docked molecules class

        Attributes
        ----------
        entries : list
            'remarks' : dict
                str : float / int
            'internal' : dict
                'object' : str
                'state' : int
        headers : list

        Properties
        ----------
        n_entries : int
        objects : set
        remarks : set
    """

    internal_empty = {'object':'', 'state': 0}

    def __init__(self):
        self.entries = []       # list of dict for every docked entry
        # default table headers
        self.headers = [
                        'Cluster', 'ClusterRank', 'deltaG',     # Swiss-Dock
                        'RANK', 'Total',                        # pyDock
                        'value'                                 # generic
                        ]

    @property
    def n_entries(self) -> int:
        return len(self.entries)

    @property
    def objects(self) -> set:
        return {i['internal']['object'] for i in self.entries}

    @property
    def remarks(self) -> set:
        if not self.entries:
            return set()
        else:
            # get all readed REMARKs
            return {j for i in self.entries for j in i['remarks'].keys()}

    def clear(self):
        """Remove all the objects related to the class and clear it's entries"""
        for obj in self.objects:
            cmd.delete(obj)
        self.__init__()

    def remove_ndx(self, ndx, update=True):
        """
            Remove a stored entry / pdb coordinates based on index

            Paramenters
            -----------
            ndx : int
                index of entry to remove
            update : bool
                update entries by decrement 'state' of same 'object' and 'ClusterRank' of same 'Cluster'
        """

        entry = self.entries[ndx]
        if update and 'Cluster' in self.remarks and 'ClusterRank' in self.remarks:
            for e in self.entries:
                if e['remarks']['Cluster'] == entry['remarks']['Cluster']:
                    e['remarks']['ClusterRank'] = e['remarks']['ClusterRank'] - int(e['remarks']['ClusterRank'] > entry['remarks']['ClusterRank'])
                if e['internal']['object'] == entry['internal']['object']:
                    e['internal']['state'] = e['internal']['state'] - int(e['internal']['state'] > entry['internal']['state'])
        del self.entries[ndx]

    def load_dock4(self, cluster, object, mode):
        """
            Load a SwissDock's cluster of ligands from string list in PDB >Dock4 format

            Parameters
            ----------
            cluster : list of str
                list of string lines from cluster of structures in PDB format
            object : str
                name to be include the new object
            mode : {0, 1, 2}
                0 - all molecules to same object
                1 - only first molecule of each cluster to object (ClusterRank==0)
                2 - all molecules to multiple objects according to clusters
        """

        cluster = [line.strip() for line in cluster if line.strip()]

        self.__init__()

        # read all structures remarks/coordinates
        i = 0
        pdb = []
        remark_re = re.compile(r'(?i)^REMARK\b\s+(\w+)\s*:\s*(-?\d+\.?\d*)')
        while i < len(cluster):

            pdb_keyword = cluster[i].split()[0].upper()

            # process docking information in REMARKs
            if pdb_keyword == 'REMARK':
                remarks = dict()
                # loop over REMARKs until no compliant found
                while remark_re.match(cluster[i]):
                    match = remark_re.match(cluster[i])
                    key = str(match.group(1))
                    value = float(match.group(2)) if key not in ('Cluster', 'ClusterRank') else int(match.group(2))
                    remarks[key] = value
                    i += 1

            # take whole molecule PDB coordinate lines
            elif pdb_keyword in ('ATOM', 'HETATM'):
                i_0 = i
                while cluster[i].split()[0].upper() in ('ATOM', 'HETATM'):
                    i += 1
                pdb_molecule = "\n".join(cluster[i_0:i]) + '\nENDMDL\n'

                # append to main attribute at the end of molecule
                pdb.append(pdb_molecule)
                self.entries.append({'remarks':remarks, 'internal':deepcopy(self.internal_empty)})

            else:
                i += 1

        # equalize remarks for all entries
        for n, i in enumerate(self.entries):
            for j in self.remarks:
                i['remarks'].setdefault(j, None)
            # set internals
            i['internal']['object'] = object
            i['internal']['state'] = n + 1

        # check if defined Cluster and ClusterRank
        if mode in ('1', '2') and not 'Cluster' in self.remarks or not 'ClusterRank' in self.remarks:
            print(" PyViewDock: Failed splitting while loading. Missing 'Cluster' or 'ClusterRank'.")
            return

        # load only first of every cluster (ClusterRank == 0)
        if mode == '1':
            entries_tmp, pdb_tmp = [], []
            n_state = 0
            for e,p in zip(self.entries, pdb):
                if e['remarks']['ClusterRank'] == 0:
                    pdb_tmp.append(p)
                    entries_tmp.append(e)
                    n_state += 1
                    entries_tmp[-1]['internal']['state'] = n_state

            self.entries, pdb = deepcopy(entries_tmp), deepcopy(pdb_tmp)
            cmd.read_pdbstr("".join(pdb), object)

        # load all in different objects by Cluster
        elif mode == '2':
            pdb_tmp = dict()
            for e,p in zip(self.entries, pdb):
                object_new = object + '-' + str(e['remarks']['Cluster'])
                pdb_tmp.setdefault(object_new, []).append(p)
                e['internal']['object'] = object_new
                e['internal']['state'] = len(pdb_tmp[object_new]) + 1
            for object_new, p in pdb_tmp.items():
                cmd.read_pdbstr("".join(p), object_new)

        # load all in one object
        else:
            cmd.read_pdbstr("".join(pdb), object)

    def load_pydock(self, filename, object, max_n):
        """
            Load a PyDock's group of structures as an object
            with multiple states and read the docking information

            Parameters
            ----------
            filename : str
                energy resume file (.ene / .eneRST)
            object : str
                basename to include the new objects (_rec / _lig)
            max_n : int
                maximum number of structures to load
        """

        self.__init__()

        rec_obj = object+"_rec"
        lig_obj = object+"_lig"

        basename = os.path.basename(filename).split('.')[0]
        directory = os.path.dirname(os.path.realpath(filename))

        # get list of matching pdb files
        pdb_files = glob.glob(os.path.join(directory, "*.pdb"))

        # find receptor and ligand files
        try:
            receptor_file = [i for i in pdb_files if "_rec.pdb" in i][0]
            ligand_file = [i for i in pdb_files if "_lig.pdb" in i][0]
        except:
            print(" PyViewDock: Failed loading pyDock file. Missing '_rec.pdb' or '_lig.pdb'.")
            return

        # read energy file
        with open(filename, "rt") as f:
            energy_file = [line.strip() for line in f.readlines() if line.strip() and not line.startswith("----")]
            header = energy_file.pop(0).split()
            for line in energy_file:
                remarks = { h:(int(v) if h in {'Conf', 'RANK'} else float(v)) for h,v in zip(header, line.split())}
                self.entries.append({'remarks':deepcopy(remarks), 'internal':deepcopy(self.internal_empty)})

        # load receptor
        importing.load(receptor_file, rec_obj)

        # load ligands
        loaded = []
        not_found_warning = False
        for n, entry in enumerate(self.entries):
            if n+1 > max_n: break
            conf_num = entry['remarks']['Conf']
            try:
                conf_file = [i for i in pdb_files if f"_{conf_num}.pdb" in i][0]
            except IndexError:
                not_found_warning = True
                continue
            else:
                loaded.append(n)
                entry['internal']['object'] = lig_obj
                entry['internal']['state'] = len(loaded)
                importing.load(conf_file, lig_obj, 0)

        if not_found_warning: print(" PyViewDock: WARNING: Some ligands defined on the energy file could not been found and loaded.")

        # delete entries which pdb has not been found
        for i in reversed(range(self.n_entries)):
            if i not in loaded: del self.entries[i]

        # remove atoms of receptor from ligand
        cmd.remove(f"{lig_obj} in {rec_obj}")

    def load_xyz(self, filename, object):
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

        self.__init__()

        # read comments from xyz file
        with open(filename, 'rt') as f:
            xyz_file = f.readlines()
        nline = 0
        comments = []
        while nline < len(xyz_file):
            natoms = int(xyz_file[nline])
            comments.append(xyz_file[nline+1].strip())
            nline += natoms+2

        # process comments
        # TODO: broader processing and pattern recognition
        if all(isinstance(i, float) for i in comments):
            comments = [float(i) for i in comments]

        # add entries to data class
        for n, comm in enumerate(comments):
            remarks = {'value': comm}
            self.entries.append({'internal': {'object': object, 'state': n+1},
                                 'remarks': remarks})

        # load structures into PyMOL
        importing.load(filename, object=object, format='xyz', quiet=1)

    def export_data(self, filename, format=None):
        """
            Save file containing docked data of all entries

            Parameters
            ----------
            filename : str
                data output file
            format : {'csv', 'txt', None}, optional
                file format, default is None and guessed from filename's suffix
                csv : semicolon separated data
                txt : space separated data, with the header row preceded by '#'
        """

        if self.n_entries == 0:
            print(f" PyViewDock: No docked entries found.")
            return

        # guess format
        if not format:
            format = os.path.basename(filename).rpartition('.')[-1].lower()
        # check supported format
        format = format.lower()
        if not format in {'csv', 'txt'}:
            raise ValueError("Unknown file format")

        # build data
        remarks = list(self.entries[0]['remarks'].keys())
        joiner = ";" if format=='csv' else "  "
        data = [joiner.join(remarks)+"\n"]
        for entry in self.entries:
            data_entry = [str(entry['remarks'][r]) for r in remarks]
            data.append(joiner.join(data_entry)+"\n")

        # write data file
        with open(filename, 'w', encoding='utf-8') as f:
            if format=='txt': f.write('#  '+data.pop(0))
            f.writelines(data)

        print(f" PyViewDock: Data exported to \"{filename}\" as \"{format}\".")

    def sort(self, remark, reverse=False):
        """
            Sort entries according to values of 'remark'

            Parameters
            ----------
            remark : str
                field to use as sorting guide
            reverse : bool
                direction of sorting (False/True : Ascending/Descending)
        """

        if remark not in self.remarks:
            raise ValueError("Unkown 'remark' to sort by")

        self.entries = sorted(self.entries, key=lambda k: k['remarks'][remark], reverse=reverse)


def get_docked() -> 'Docked':
    """Get 'Docked' class from current session or initialize a new one"""
    from pymol import session
    if not 'PyViewDock' in vars(session):
        session.PyViewDock = Docked()
    return session.PyViewDock


##  FUNCTIONS  ########################################################

def non_repeated_object(object):
    """
        Get an object name that is not used in the current session
        If the provided name is present, add a numeric suffix
        i.e.: object_name -> object_name_1, object_name_2, ...

        Parameters
        ----------
        object : str
            name of the object to be checked

        Returns
        -------
        str
            name that is not used in the current session
    """
    current_objects = cmd.get_names('objects')
    if object in current_objects:
        n = 2
        while f"{object}_{n}" in current_objects:
            n += 1
        print(f" PyViewDock: New object name colliding with existing. \"{object}\" changed to \"{object}_{n}\"")
        return f"{object}_{n}"
    else:
        return object


def load_dock4(filename, object='', mode=0):
    """
        Load a SwissDock's cluster of ligands as an object
        with multiple states and read the docking information

        Parameters
        ----------
        filename : str
            cluster of structures in PDB format
        object : str
            name to be include the new object
            if absent, taken from filename
        mode : {0, 1, 2}
            0 - all molecules to same object
            1 - only first molecule of each cluster to object
            2 - all molecules to multiple objects according to clusters
    """

    docked = get_docked()

    if not object:
        object = os.path.basename(filename).split('.')[0]
    object = non_repeated_object(object)

    # read file as list of strings
    with open(filename, "rt") as f:
        cluster = f.readlines()

    docked.load_dock4(cluster, object, mode)
    print(f" PyViewDock: \"{filename}\" loaded as \"{object}\"")


def load_chimerax(filename):
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
        print(" PyViewDock: Failed reading 'chimerax' file. File not found.")
    except:
        print(" PyViewDock: Failed reading 'chimerax' file. Invalid format.")
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


def load_pydock(filename, object='', max_n=100):
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


def load_xyz(filename, object=''):
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


def export_docked_data(filename, format=''):
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

def set_name_catcher(old_name, new_name, _self=cmd):
    """
        Change the name of an object or selection.

        This implementation is exact to the original
        But necessary to catch any renaming and
        update the corresponding docked entries
    """

    r = cmd.DEFAULT_ERROR
    try:
        _self.lock(_self)
        r = cmd._cmd.set_name(_self._COb, str(old_name), str(new_name))
    except:
        pass
    else:
        # TODO: update objects for docked entries
        pass
    finally:
        _self.unlock(r,_self)
    if _self._raising(r,_self): raise CmdException
    return r
