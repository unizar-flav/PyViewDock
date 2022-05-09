"""
  Miscellaneous and utility functions
  ===================================

  Functions
  ---------
    non_repeated_object
    set_name_catcher

"""

from pymol import cmd, CmdException

from .docked import get_docked


def non_repeated_object(object:str) -> str:
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
        docked = get_docked()
        docked.modify_entries('object', old_name, new_name)
    finally:
        _self.unlock(r,_self)
    if _self._raising(r,_self): raise CmdException
    return r
