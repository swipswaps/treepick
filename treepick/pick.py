import os
import cgitb
import curses
import pdb
import readline
import sys
from .paths import Paths
from .keys import parse
from .color import Color

# Get more detailed traceback reports
cgitb.enable(format="text")  # https://pymotw.com/2/cgitb/


def draw(parent, action, curline, picked, expanded, sized):
    line = 0
    getsizeall = False
    for child, depth in parent.traverse():
        if depth == 0:
            continue  # don't draw root node
        if line == curline:
            if action == 'expand':
                expanded.add(child.name)
                curline += 1
            elif action == 'collapse':
                if child.expanded:
                    expanded.remove(child.name)
            elif action == 'expand_all':
                for c, d in child.traverse():
                    # only expand one level at a time
                    if d > 1:
                        continue
                    expanded.add(c.name)
            elif action == 'collapse_all':
                curline = child.collapse_all(parent, curline, depth)
            elif action == 'toggle_expand':
                if child.expanded:
                    expanded.remove(child.name)
                else:
                    expanded.add(child.name)
            elif action == 'toggle_mark':
                if child.name in picked:
                    picked.remove(child.name)
                else:
                    picked.add(child.name)
                curline += 1
            elif action == 'next_parent':
                curline += child.nextparent(parent, curline, depth)
            elif action == 'prev_parent':
                curline = child.prevparent(parent, curline, depth)[0]
            elif action == 'get_size':
                sized.add(child.name)
                curline += 1
            elif action == 'get_size_all':
                getsizeall = True
            action = None  # reset action
        line += 1  # keep scrolling!

    parent.drawall(curline, getsizeall)
    return picked, expanded, line, curline


def header(screen):
    msg = "Use arrow keys, Vi [h,j,k,l], or Emacs [b,f,p,n] keys to navigate"
    try:
        screen.addstr(msg)
        screen.chgat(0, 19, 9, curses.A_BOLD | curses.color_pair(3))
        screen.chgat(0, 39, 9, curses.A_BOLD | curses.color_pair(3))
    except:
        pass


def footer(screen):
    msg = "[SPC] toggle mark, [?] show all keybindings, [q] to quit."
    try:
        l = curses.LINES - 1
        screen.addstr(l, 0, msg)
        screen.chgat(l, 0, 5, curses.A_BOLD | curses.color_pair(3))
        screen.chgat(l, 19, 3, curses.A_BOLD | curses.color_pair(3))
        screen.chgat(l, 45, 3, curses.A_BOLD | curses.color_pair(3))
    except:
        pass


def body(screen):
    win = curses.newwin(curses.LINES - 3, curses.COLS, 2, 0)
    screen.refresh()
    return win


def reset(win, root, hidden):
    expanded, picked, sized = (set() for i in range(3))
    parent = Paths(win, root, hidden, picked, expanded, sized)
    action = None
    curline = 0
    return expanded, picked, sized, parent, action, curline


def init(screen):
    curses.curs_set(0)  # get rid of cursor
    header(screen)
    footer(screen)


def pick(screen, root, hidden):
    init(screen)
    Color(screen)
    win = body(screen)
    expanded, picked, sized, parent, action, curline = reset(win, root, hidden)

    while True:
        # to reset or toggle view of dotfiles we need to create a new Path
        # object before erasing the screen & descending into draw function.
        if action == 'reset':
            expanded, picked, sized, parent, action, curline = reset(
                win, root, hidden)
        elif action == 'toggle_hidden':
            if hidden:
                hidden = False
            else:
                hidden = True
            sized = set()  # too costly to keep
            parent = Paths(win, root, hidden, picked, expanded, sized)
            action = None

        parent.expand()

        win.erase()  # https://stackoverflow.com/a/24966639 - prevent flashes

        picked, expanded, line, curline = draw(
            parent, action, curline, picked, expanded, sized)

        win.refresh()

        action, curline = parse(win, curline, line)

        if action == 'quit':
            return picked
