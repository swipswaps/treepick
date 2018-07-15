import cgitb
import curses
import os
import pdb
import readline
import sys

from paths import Paths
from keys import parse_keys

# Get more detailed traceback reports
cgitb.enable(format="text")  # https://pymotw.com/2/cgitb/


def pick(stdscr, root, hidden):
    picked = []
    parent = Paths(stdscr, root, hidden, picked)
    parent.expand()
    curline = 0
    action = None

    while True:
        line = 0

        # to reset or toggle view of dotfiles we need to create a new Path
        # object before, erasing the screen & descending into draw loop.
        if action == 'reset':
            picked = []
            parent = Paths(stdscr, root, hidden, picked)
            parent.expand()
            action = None
        elif action == 'toggle_hidden':
            if hidden:
                hidden = False
            else:
                hidden = True
            parent = Paths(stdscr, root, hidden, picked)
            parent.expand()
            action = None
            # restore marked state
            for child, depth in parent.traverse():
                if child.name in picked:
                    child.mark()

        stdscr.erase()  # https://stackoverflow.com/a/24966639 - prevent flashes

        for child, depth in parent.traverse():
            if depth == 0:
                continue  # don't draw root node
            if line == curline:
                # picked line needs to be different than default
                child.colors.curline(child.name)

                if action == 'expand':
                    child.expand()
                    child.colors.default(child.name)
                    curline += 1
                elif action == 'collapse':
                    child.collapse()
                elif action == 'expand_all':
                    for c, d in child.traverse():
                        # only expand one level at a time
                        if d > 1:
                            continue
                        c.expand()
                elif action == 'collapse_all':
                    pass
                elif action == 'toggle_expand':
                    if child.expanded:
                        child.collapse()
                    else:
                        child.expand()
                elif action == 'toggle_mark':
                    if child.marked:
                        child.marked = False
                        picked.remove(child.name)
                        child.colors.default(child.name)
                    else:
                        child.marked = True
                        picked.append(child.name)
                        child.colors.yellow_black()
                    curline += 1
                elif action == 'next_parent':
                    curline += child.nextparent(parent, curline, depth)
                elif action == 'prev_parent':
                    curline = child.prevparent(parent)
                elif action == 'get_size':
                    child.getsize = True
                    child.colors.default(child.name)
                    curline += 1
                elif action == 'get_size_all':
                    for c, d in parent.traverse():
                        c.getsize = True
                action = None  # reset action

            else:
                child.colors.default(child.name)

            child.drawlines(depth, curline, line)

            child.getsize = False  # stop computing sizes!
            line += 1  # keep scrolling!

        stdscr.refresh()

        results = parse_keys(stdscr, curline, line)
        if results:
            action = results[0]
            curline = results[1]
        else:
            return picked
