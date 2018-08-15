# Copyright (c) 2018, Toby Slight. All rights reserved.
# ISC License (ISCL) - see LICENSE file for details.

import os
import cgitb
from .paths import Paths
from .keys import Keys

# Get more detailed traceback reports
cgitb.enable(format="text")  # https://pymotw.com/2/cgitb/


def process(parent, action):
    '''
    Traverse parent object & process the action returned from keys.parse
    '''
    line = 0
    for child, depth in parent.traverse():
        if depth == 0:
            continue  # don't process root node
        if line == parent.curline:
            if action == 'expand':
                child.expand()
            elif action == 'expand_all':
                child.expand(recurse=True)
            elif action == 'toggle_expand':
                child.expand(toggle=True)
            elif action == 'collapse':
                child.collapse(parent, depth)
            elif action == 'collapse_all':
                child.collapse(parent, depth, recurse=True)
            elif action == 'toggle_pick':
                child.pick()
            elif action == 'pickall':
                child.pick(parent)
            elif action == 'nextparent':
                child.nextparent(parent, depth)
            elif action == 'prevparent':
                child.prevparent(parent, depth)[0]
            elif action == 'getsize':
                child.getsize(parent)
            elif action == 'getsizeall':
                child.getsize(parent, sizeall=True)
            action = None  # reset action
        line += 1  # keep scrolling!
    return line


def get_picked(relative, root, picked):
    if relative:
        if root.endswith(os.path.sep):
            length = len(root)
        else:
            length = len(root + os.path.sep)
        return [p[length:] for p in picked]
    return picked


def reset(scr, root, hidden, picked):
    parent = Paths(scr, root, hidden, picked=picked,
                   expanded=set([root]), sized=dict())
    action = None
    return parent, action


def pick(stdscr, root, hidden=True, relative=False, picked=[]):
    picked = [root + p for p in picked]
    keys = Keys(stdscr, picked)
    parent, action = reset(stdscr, root, hidden, picked)
    matches = []
    while True:
        # to reset or toggle view of dotfiles we need to create a new Path
        # object before erasing the screen & descending into process function.
        line = parent.drawtree(action)
        if action == 'reset':
            parent, action = reset(stdscr, root, hidden, picked=[])
        elif action == 'resize':
            parent.resize()
        elif action == 'toggle_hidden':
            parent.toggle_hidden()
        elif action == 'find':
            string = parent.mktbfooter("Find: ").strip()
            if string:
                matches = parent.find(string)
        elif action == 'findnext':
            parent.findnext(matches)
        elif action == 'findprev':
            parent.findprev(matches)
        elif action == 'match':
            globs = parent.mktbfooter("Pick: ").strip().split()
            if globs:
                parent.pick(parent, globs)
        elif action == 'quit':
            return get_picked(relative, root, parent.picked)
        action, parent.curline = keys.getkeys(parent.curline, line)
