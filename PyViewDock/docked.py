"""
  'Docked' Structures Class
  =========================

  Classes
  -------
    Docked

  Functions
  ---------
    set_docked
    get_docked

"""

import glob
import os
import re
from copy import deepcopy

from pymol import cmd, importing, CmdException

from . import __version__
from . import misc


def set_docked(docked:'Docked') -> None:
    """
        Set 'docked' dictionary to current session
        from a 'Docked' object.

        Parameters
        ----------
        docked : Docked
            'Docked' object
    """
    from pymol import session
    session.PyViewDock = docked.data

def get_docked() -> 'Docked':
    """
        Get 'docked' dictionary from current session
        or initialize a new one and return a 'Docked'
        object from it.

        Returns
        -------
        Docked
            'Docked' object
    """
    from pymol import session
    if not 'PyViewDock' in vars(session):
        docked = Docked()
    else:
        if isinstance(session.PyViewDock, dict):
            session_PyViewDock = session.PyViewDock
        else:
            # object directly saved for retro-compatibility
            session_PyViewDock = {'version': '0.3.1',   # last version to save whole class
                                  'entries': session.PyViewDock.entries,
                                  'headers': session.PyViewDock.headers}
        docked = Docked(session_PyViewDock)
    return docked

class Docked():
    """
        Group of docked molecules class

        Parameters
        ----------
        session_PyViewDock : dict
            dictionary with 'Docked' data saved
            in the current session to be used

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
        entries_unified : list
        objects : set
        remarks : set
        data : dict
    """

    version = __version__
    internal_empty = {'object':'', 'state': 0}

    def __init__(self, session_PyViewDock:dict=None) -> None:
        self.entries = []       # list of dict for every docked entry
        # default table headers
        self.headers = [
                        'Cluster', 'ClusterRank', 'deltaG',     # Swiss-Dock
                        'RANK', 'Total',                        # pyDock
                        'structure', 'value'                    # generic
                        ]
        if session_PyViewDock:
            self.entries = session_PyViewDock['entries']
            self.headers = session_PyViewDock['headers']
        set_docked(self)

    @property
    def n_entries(self) -> int:
        return len(self.entries)

    @property
    def entries_unified(self) -> list:
        """
            Return entries as a list of a unified dictionary,
            joining 'remarks' and 'internal'
        """
        return [{**entry['internal'], **entry['remarks']} for entry in self.entries]

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

    @property
    def data(self) -> dict:
        """Return docked data as a dictionary to be saved in a session"""
        return {
            'version': self.version,
            'entries': self.entries,
            'headers': self.headers
            }

    def clear(self) -> None:
        """Remove all the objects related to the class and clear it's entries"""
        for obj in self.objects:
            cmd.delete(obj)
        self.__init__()

    def equalize_remarks(self) -> None:
        """
            Add to all entries the same remarks,
            with None value if not previously set
        """
        all_remarks = self.remarks
        for entry in self.entries:
            for remark in all_remarks:
                entry['remarks'].setdefault(remark, None)

    def findall(self, match_all=True, **remarks_and_values) -> list:
        """
            Find a list of entry index that match all/any remarks

            Parameters
            ----------
            match_all : bool
                if True, all remarks must match, otherwise any
            remarks_and_values : **kwargs
                key : str
                    remark to match
                value : float / int / str
                    value to match

            Returns
            -------
            list
                list of index of entries that match
        """
        # check input fields
        if remarks_and_values.keys() - self.remarks - {'object', 'state'}:
            raise ValueError("Not valid remark provided")
        # find any/all entries that match
        matcher = all if match_all else any
        return [n for n, entry in enumerate(self.entries_unified)
                if matcher(entry[key] == value for key, value in remarks_and_values.items())]

    def find(self, match_all=True, **remarks_and_values) -> int:
        """
            Find the index of the first entry that match all/any remarks

            Parameters
            ----------
            match_all : bool
                if True, all remarks must match, otherwise any
            remarks_and_values : **kwargs
                key : str
                    remark to match
                value : float / int / str
                    value to match

            Returns
            -------
            int
                index of entry that match, None if not found
        """
        matching_index = self.findall(match_all=match_all, **remarks_and_values)
        if matching_index:
            return matching_index[0]
        else:
            return None

    def remove_ndx(self, ndx, update=True) -> None:
        """
            Remove a stored entry and state based on index

            Paramenters
            -----------
            ndx : int
                index of entry to remove
            update : bool
                update entries by decrement 'state' of same 'object'
        """
        object = self.entries[ndx]['internal']['object']
        state = self.entries[ndx]['internal']['state']
        del self.entries[ndx]
        tmp_object = misc.non_repeated_object("tmp")
        cmd.create(tmp_object, f"object {object}", zoom=0, quiet=1)
        cmd.delete(object)
        for entry in [self.entries[n] for n in self.findall(object=object)]:
            entry_state = entry['internal']['state']
            cmd.create(object, f"object {tmp_object}", source_state=entry_state, target_state=-1, zoom=0, quiet=1, extract=None)
            if update:
                entry['internal']['state'] -= int(entry_state > state)
        cmd.delete(tmp_object)

    def remove(self, match_all=True, **remarks_and_values) -> None:
        """
            Remove entries that match all/any remarks

            Parameters
            ----------
            match_all : bool
                if True, all remarks must match, otherwise any
            remarks_and_values : **kwargs
                key : str
                    remark to match
                value : float / int / str
                    value to match
        """
        matching_index = self.findall(match_all=match_all, **remarks_and_values)
        for n in sorted(matching_index, reverse=True):
            self.remove_ndx(n)

    def remove_without_objects(self) -> None:
        """
            Delete the entries without object in PyMOL
        """
        for object_to_remove in self.objects - set(cmd.get_names('objects')):
            self.remove(object=object_to_remove)

    def modify_entries(self, remark, old_value, new_value) -> None:
        """
            Change values of a remark of all entries that matches the old value

            Parameters
            ----------
            remark : str
                remark to change, special treatment for 'object' and 'state'
            old_value : float / int / str
                current value of the remark to match and change
            new_value : float / int / str
                new value for the remark
        """
        section = 'internal' if remark in ['object', 'state'] else 'remarks'
        for entry in self.entries:
            if entry[section][remark] == old_value:
                entry[section][remark] = new_value

    def copy_to_object(self, ndx, object, extract=False) -> None:
        """
            Copy an entry to a new object

            Parameters
            ----------
            ndx : int
                index of entry to copy
            object : str
                name of the new object
            extract : bool
                extract the entry from the original object
        """
        entry = self.entries[ndx]
        self.entries.append(deepcopy(entry))
        self.entries[-1]['internal']['object'] = object
        self.entries[-1]['internal']['state'] = 1
        cmd.create(object,
                   f"object {entry['internal']['object']}",
                   source_state=entry['internal']['state'],
                   target_state=1,
                   zoom=0,
                   quiet=1,
                   extract=False)
        if extract:
            self.remove_ndx(ndx)

    def load_dock4(self, cluster, object, mode) -> None:
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

        # read all structures remarks/coordinates
        i = 0
        pdb = []
        entries = []
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
                entries.append({'remarks':remarks, 'internal':deepcopy(self.internal_empty)})

            else:
                i += 1

        # set internals
        for n, i in enumerate(entries):
            i['internal']['object'] = object
            i['internal']['state'] = n + 1

        # load only first of every cluster (ClusterRank == 0)
        if mode == '1':
            # check that all entries has ClusterRank remark
            if not all(['ClusterRank' in i['remarks'] for i in entries]):
                raise CmdException("Failed splitting while loading. Missing 'ClusterRank'.", "PyViewDock")
            entries_tmp, pdb_tmp = [], []
            n_state = 0
            for e,p in zip(entries, pdb):
                if e['remarks']['ClusterRank'] == 0:
                    pdb_tmp.append(p)
                    entries_tmp.append(e)
                    n_state += 1
                    entries_tmp[-1]['internal']['state'] = n_state

            entries, pdb = deepcopy(entries_tmp), deepcopy(pdb_tmp)
            cmd.read_pdbstr("".join(pdb), object)

        # load all in different objects by Cluster
        elif mode == '2':
            # check that all entries has Cluster remark
            if not all(['Cluster' in i['remarks'] for i in entries]):
                raise CmdException("Failed splitting while loading. Missing 'Cluster'.", "PyViewDock")
            pdb_tmp = dict()
            for e,p in zip(entries, pdb):
                object_new = object + '-' + str(e['remarks']['Cluster'])
                pdb_tmp.setdefault(object_new, []).append(p)
                e['internal']['object'] = object_new
                e['internal']['state'] = len(pdb_tmp[object_new]) + 1
            for object_new, p in pdb_tmp.items():
                cmd.read_pdbstr("".join(p), object_new)

        # load all in one object
        else:
            cmd.read_pdbstr("".join(pdb), object)

        self.entries.extend(entries)
        self.equalize_remarks()

    def load_pydock(self, filename, object, max_n) -> None:
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
            raise CmdException("Failed loading pyDock file. Missing '_rec.pdb' or '_lig.pdb'.", "PyViewDock")

        # read energy file
        entries = []
        with open(filename, "rt") as f:
            energy_file = [line.strip() for line in f.readlines() if line.strip() and not line.startswith("----")]
            header = energy_file.pop(0).split()
            for line in energy_file:
                remarks = { h:(int(v) if h in {'Conf', 'RANK'} else float(v)) for h,v in zip(header, line.split())}
                entries.append({'remarks':deepcopy(remarks), 'internal':deepcopy(self.internal_empty)})

        # load receptor
        importing.load(receptor_file, rec_obj)

        # load ligands
        loaded = []
        not_found_warning = False
        for n, entry in enumerate(entries):
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

        if not_found_warning:
            print(" PyViewDock: WARNING! Some ligands defined on the energy file could not been found and loaded.")

        # delete entries which pdb has not been found
        for i in reversed(range(len(entries))):
            if i not in loaded: del entries[i]

        self.entries.extend(entries)
        self.equalize_remarks()

        # remove atoms of receptor from ligand
        cmd.remove(f"{lig_obj} in {rec_obj}")

    def load_xyz(self, filename, object) -> None:
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
            remarks = {'structure': n+1, 'value': comm}
            self.entries.append({'internal': {'object': object, 'state': n+1},
                                 'remarks': remarks})
        self.equalize_remarks()

        # load structures into PyMOL
        importing.load(filename, object=object, format='xyz', quiet=1)

    def export_data(self, filename, format=None) -> None:
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
            raise CmdException("No docked entries found to export.", "PyViewDock")

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

    def sort(self, remark, reverse=False) -> None:
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
