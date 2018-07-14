import argparse
import cgitb
import curses
import os
import pdb
import readline
import sys

from paths import Paths

# Get more detailed traceback reports
cgitb.enable(format="text")  # https://pymotw.com/2/cgitb/


def parse_keys(stdscr, curline, line):
    ESC = 27
    action = None
    ch = stdscr.getch()
    if ch == ord('e') or ch == ord('q') or ch == ESC:
        return
    elif ch == ord('r'):
        action = 'reset'
    elif ch == ord('.'):
        action = 'toggle_hidden'
    elif ch == curses.KEY_RIGHT or ch == ord('l') or ch == ord('f'):
        action = 'expand'
    elif ch == curses.KEY_LEFT or ch == ord('h') or ch == ord('b'):
        action = 'collapse'
    elif ch == ord('L') or ch == ord('F'):
        action = 'expand_all'
    elif ch == ord('H') or ch == ord('B'):
        action = 'collapse_all'
    elif ch == ord('\t') or ch == ord('\n'):
        action = 'toggle_expand'
    elif ch == ord('m') or ch == ord(' '):
        action = 'toggle_mark'
    elif ch == ord('J') or ch == ord('N'):
        action = 'next_parent'
    elif ch == ord('K') or ch == ord('P'):
        action = 'prev_parent'
    elif ch == ord('s') or ch == ord('?'):
        action = 'get_size'
    elif ch == ord('S'):
        action = 'get_size_all'
    elif ch == curses.KEY_UP or ch == ord('k') or ch == ord('p'):
        curline -= 1
    elif ch == curses.KEY_DOWN or ch == ord('j') or ch == ord('n'):
        curline += 1
    elif ch == curses.KEY_UP or ch == ord('k') or ch == ord('p'):
        curline -= 1
    elif ch == curses.KEY_DOWN or ch == ord('j') or ch == ord('n'):
        curline += 1
    elif ch == curses.KEY_PPAGE or ch == ord('u') or ch == ord('V'):
        curline -= curses.LINES
        if curline < 0:
            curline = 0
    elif ch == curses.KEY_NPAGE or ch == ord('d') or ch == ord('v'):
        curline += curses.LINES
        if curline >= line:
            curline = line - 1
    elif ch == curses.KEY_HOME or ch == ord('g') or ch == ord('<'):
        curline = 0
    elif ch == curses.KEY_END or ch == ord('G') or ch == ord('>'):
        curline = line - 1
    curline %= line
    return action, curline


def select(stdscr, root, hidden):
    selected = []
    parent = Paths(stdscr, root, hidden, selected)
    parent.expand()
    curline = 0
    action = None

    while True:
        line = 0

        # to reset or toggle view of dotfiles we need to create a new Path
        # object before, erasing the screen & descending into draw loop.
        if action == 'reset':
            selected = []
            parent = Paths(stdscr, root, hidden, selected)
            parent.expand()
            action = None
        elif action == 'toggle_hidden':
            if hidden:
                hidden = False
            else:
                hidden = True
            parent = Paths(stdscr, root, hidden, selected)
            parent.expand()
            action = None
            # restore marked state
            for child, depth in parent.traverse():
                if child.name in selected:
                    child.mark()

        stdscr.erase()  # https://stackoverflow.com/a/24966639 - prevent flashes

        for child, depth in parent.traverse():
            if depth == 0:
                continue  # don't draw root node
            if line == curline:
                # selected line needs to be different than default
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
                        selected.remove(child.name)
                        child.colors.default(child.name)
                    else:
                        child.marked = True
                        selected.append(child.name)
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
            return selected
