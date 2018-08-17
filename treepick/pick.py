# Copyright (c) 2018, Toby Slight. All rights reserved.
# ISC License (ISCL) - see LICENSE file for details.

import os
import cgitb
from .paths import Paths

# Get more detailed traceback reports
cgitb.enable(format="text")  # https://pymotw.com/2/cgitb/


def get_picked(relative, root, picked):
    if relative:
        if root.endswith(os.path.sep):
            length = len(root)
        else:
            length = len(root + os.path.sep)
        return [p[length:] for p in picked]
    return picked


def pick(screen, root, hidden=True, relative=False, picked=[]):
    picked = [root + p for p in picked]
    parent = Paths(screen, root, hidden, picked=picked, expanded=set([root]))
    while True:
        # TODO: Get to the following point:
        # parent.getkeys()
        # parent.parsekey()
        # if parent.action == 'quit':
        #     return parent.picked
        # parent.drawtree

        if parent.action == 'reset':
            parent = Paths(screen, root, hidden,
                           picked=[], expanded=set([root]))
        elif parent.action == 'quit':
            return get_picked(relative, root, parent.picked)
        parent.process_parent()
        parent.process_curline()
        parent.drawtree()
        parent.getkeys()
