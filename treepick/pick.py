# Copyright (c) 2018, Toby Slight. All rights reserved.
# ISC License (ISCL) - see LICENSE file for details.

import os
import cgitb
from .paths import Paths
from .screen import Screen
from .keys import Keys

# Get more detailed traceback reports
cgitb.enable(format="text")  # https://pymotw.com/2/cgitb/


def process(parent, action, curline):
    '''
    Traverse parent object & process the action returned from keys.parse
    '''
    line = 0
    for child, depth in parent.traverse():
        if depth == 0:
            continue  # don't process root node
        if line == curline:
            if action == 'expand':
                curline = child.expand(curline)
            elif action == 'expand_all':
                curline = child.expand(curline, recurse=True)
            elif action == 'toggle_expand':
                curline = child.expand(curline, toggle=True)
            elif action == 'collapse':
                curline = child.collapse(parent, curline, depth)
            elif action == 'collapse_all':
                curline = child.collapse(parent, curline, depth, recurse=True)
            elif action == 'toggle_pick':
                curline = child.pick(curline)
            elif action == 'pickall':
                curline = child.pick(curline, parent)
            elif action == 'nextparent':
                curline = child.nextparent(parent, curline, depth)
            elif action == 'prevparent':
                curline = child.prevparent(parent, curline, depth)[0]
            elif action == 'getsize':
                curline = child.getsize(curline, parent)
            elif action == 'getsizeall':
                curline = child.getsize(curline, parent, sizeall=True)
            action = None  # reset action
        line += 1  # keep scrolling!
    return curline, line


def get_picked(relative, root, picked):
    if relative:
        if root.endswith(os.path.sep):
            length = len(root)
        else:
            length = len(root + os.path.sep)
        return [p[length:] for p in picked]
    return picked


def reset(root, hidden, picked):
    parent = Paths(root, hidden, picked, expanded=set([root]), sized=dict())
    action = None
    curline = 0
    return parent, action, curline


def pick(stdscr, root, hidden=True, relative=False, picked=[]):
    picked = [root + p for p in picked]
    scr = Screen(stdscr, picked)
    keys = Keys(stdscr, picked)
    parent, action, curline = reset(root, hidden, picked)
    matches = []
    while True:
        # to reset or toggle view of dotfiles we need to create a new Path
        # object before erasing the screen & descending into process function.
        if action == 'reset':
            parent, action, curline = reset(root, hidden, picked=[])
        elif action == 'resize':
            scr.resize()
        elif action == 'toggle_hidden':
            curline = parent.toggle_hidden(curline, scr)
        elif action == 'find':
            string = scr.mktbfooter("Find: ").strip()
            if string:
                curline, matches = parent.find(curline, string)
        elif action == 'findnext':
            curline = parent.findnext(curline, matches)
        elif action == 'findprev':
            curline = parent.findprev(curline, matches)
        elif action == 'match':
            globs = scr.mktbfooter("Pick: ").strip().split()
            if globs:
                parent.pick(curline, parent, globs)
        elif action == 'quit':
            return get_picked(relative, root, parent.picked)
        curline, line = process(parent, action, curline)
        parent.drawtree(curline, scr)
        action, curline = keys.getkeys(curline, line)
