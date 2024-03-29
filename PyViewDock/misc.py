"""
  Miscellaneous and utility functions
  ===================================

  Functions
  ---------
    non_repeated_object
    set_name_catcher
    align_multi

"""

from pymol import cmd, CmdException

from .docked import get_docked


def non_repeated_object(object:str, quiet=0) -> str:
    '''
    DESCRIPTION

        Get an object name that is not used in the current session
        If the provided name is present, add a numeric suffix

    ARGUMENTS

        object_name = string: name of the object to be checked

        quiet = 0/1: print warning message if 0 and name colliding with existing {default: 0}

    RETURNS

        string: name that is not used in the current session

    EXAMPLE

        object_name  ->  object_name  /  object_name_1, object_name_2, ...
    '''
    current_objects = cmd.get_names('objects')
    if object in current_objects:
        n = 2
        while f"{object}_{n}" in current_objects:
            n += 1
        if not quiet:
            print(f" PyViewDock: New object name colliding with existing. \"{object}\" changed to \"{object}_{n}\"")
        return f"{object}_{n}"
    else:
        return object

def set_name_catcher(old_name, new_name, _self=cmd):
    '''
    DESCRIPTION

        "set_name" changes the name of an object or selection.

    USAGE

        set_name old_name, new_name

    PYMOL API

        cmd.set_name(string old_name, string new_name)

    REMARK

        This is a re-implementation by PyViewDock and exact to
        the original, but necessary to catch any renaming and
        update the corresponding docked entries.
    '''
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

def align_multi(mobile, target, name_new='', initial_state=1, final_state=-1, source_state=1) -> None:
    '''
    DESCRIPTION

        "align_multi" aligns a single structure to every state of an existing multi-state object

    USAGE

        align_multi mobile, target [, name_new [, initial_state [, final_state [, source_state ]]]]

    ARGUMENTS

        mobile = string: name of the single structure to be aligned

        target = string: name of the existing multi-state object

        name_new = string: name of a new object to be created with the alignment, if not provided the mobile object will be overwritten {default: ''}

        initial_state = integer: initial state of the target to be aligned {default: 1}

        final_state = integer: last state of the target to be aligned, -1 to take the last existing {default: -1}

        source_state = integer: state of the mobile structure to be aligned (if more than one exists) {default: 1}

    EXAMPLES

        align_multi lig_ref, result_lig
        align_multi lig_ref, result_lig, lig_ref_aligned
    '''
    # default name_new to mobile if not provided
    print_name = f" and included as \"{name_new}\"" if name_new else ""
    name_new = name_new if name_new else mobile
    # check number of states
    target_states = cmd.count_states(target)
    final_state = target_states if final_state == -1 else final_state
    states = [max(1, initial_state), min(final_state, target_states)]
    # create a temporary object
    tmp_object = non_repeated_object("tmp", quiet=1)
    cmd.create(tmp_object, mobile, source_state=source_state)
    for n_state in range(states[0], states[1] + 1):
        cmd.align(tmp_object, target, target_state=n_state)         # align temporary object to the target
        cmd.create(name_new, tmp_object, target_state=n_state)      # append the temporary aligned object to the final object
    cmd.delete(tmp_object)
    cmd.zoom(name_new)
    print(f" PyViewDock: \"{mobile}\" aligned to \"{target}\"" + print_name)

cmd.auto_arg[0]['align_multi'] = [cmd.object_sc, 'mobile object', ', ']
cmd.auto_arg[1]['align_multi'] = [cmd.object_sc, 'target object', ', ']
cmd.auto_arg[2]['align_multi'] = [cmd.object_sc, 'new object', ', ']
