"""
  Miscellaneous and utility functions
  ===================================

  Functions
  ---------
    non_repeated_object
    set_name_catcher
    align_to_traj

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

def align_to_traj(name, mobile, target, initial_state=1, final_state=-1, source_state=1) -> None:
    """
        Create a new trajectory object by aligning a structure to every state of an existing trajectory

        Parameters
        ----------
        name : str
            name of the new trajectory object
        mobile : str
            name of the structure to be aligned
        target : str
            name of the existing trajectory object
        initial_state : int, optional
            initial state of the target trajectory to be aligned {default: 1}
        final_state : int, optional
            last state of the target trajectory to be aligned, -1 to take the last existing {default: -1}
        source_state : int, optional
            state of the mobile structure to be aligned {default: 1}
    """
    target_states = cmd.count_states(target)
    final_state = target_states if final_state == -1 else final_state
    states = [max(1, initial_state), min(final_state, target_states)]
    tmp_object = non_repeated_object("tmp")
    for n_state in range(states[0], states[1] + 1):
        cmd.create(tmp_object, mobile, source_state=source_state)   # Create a temporary object
        cmd.align(tmp_object, target, target_state=n_state)         # Align temporary object to the target
        cmd.create(name, tmp_object, target_state=-1)               # Append the temporary aligned object to the final object
        cmd.delete(tmp_object)
    print(f" PyViewDock: \"{mobile}\" aligned to \"{target}\" and included as \"{name}\"")
