import os
import cgitb
import curses
import pdb
import readline
import sys
from .paths import Paths
from .keys import parse

# Get more detailed traceback reports
cgitb.enable(format="text")  # https://pymotw.com/2/cgitb/


def draw(parent, action, curline, picked, expanded):
    line = 0  # leave space for header
    for child, depth in parent.traverse():
        if depth == 0:
            continue  # don't draw root node
        if line == curline:
            # picked line needs to be different than default
            child.color.curline(child.name)
            if action == 'expand':
                child.expand()
                expanded.append(child.name)
                child.color.default(child.name)
                curline += 1
            elif action == 'collapse':
                child.collapse()
                if child.name in expanded:
                    expanded.remove(child.name)
            elif action == 'expand_all':
                for c, d in child.traverse():
                    # only expand one level at a time
                    if d > 1:
                        continue
                    c.expand()
                    expanded.append(c.name)
            elif action == 'collapse_all':
                curline = child.collapse_all(parent, curline, depth)
            elif action == 'toggle_expand':
                if child.expanded:
                    child.collapse()
                    expanded.remove(child.name)
                else:
                    child.expand()
                    expanded.append(child.name)
            elif action == 'toggle_mark':
                if child.marked:
                    child.marked = False
                    picked.remove(child.name)
                    child.color.default(child.name)
                else:
                    child.marked = True
                    picked.append(child.name)
                    child.color.yellow_black()
                curline += 1
            elif action == 'next_parent':
                curline += child.nextparent(parent, curline, depth)
            elif action == 'prev_parent':
                curline = child.prevparent(parent, curline, depth)[0]
            elif action == 'get_size':
                child.getsize = True
                child.color.default(child.name)
                curline += 1
            elif action == 'get_size_all':
                for c, d in parent.traverse():
                    c.getsize = True
            action = None  # reset action
        else:
            child.color.default(child.name)
        child.drawlines(depth, curline, line)
        child.getsize = False  # stop computing sizes!
        line += 1  # keep scrolling!

    return picked, expanded, line, curline


def color():
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.init_pair(8, curses.COLOR_GREEN, curses.COLOR_WHITE)
    curses.init_pair(9, curses.COLOR_YELLOW, curses.COLOR_WHITE)
    curses.init_pair(10, curses.COLOR_BLUE, curses.COLOR_WHITE)
    curses.init_pair(11, curses.COLOR_MAGENTA, curses.COLOR_WHITE)
    curses.init_pair(12, curses.COLOR_CYAN, curses.COLOR_WHITE)


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
        screen.addstr(curses.LINES - 1, 0, msg)
        screen.chgat(curses.LINES - 1, 1, 5,
                     curses.A_BOLD | curses.color_pair(3))
        screen.chgat(curses.LINES - 1, 21, 3,
                     curses.A_BOLD | curses.color_pair(3))
        screen.chgat(curses.LINES - 1, 35, 3,
                     curses.A_BOLD | curses.color_pair(3))
        screen.chgat(curses.LINES - 1, 48, 3,
                     curses.A_BOLD | curses.color_pair(3))
    except:
        pass


def body(screen):
    win = curses.newwin(curses.LINES - 3, curses.COLS, 2, 0)
    screen.refresh()
    return win


def pick(screen, root, hidden):
    curses.curs_set(0)  # get rid of cursor
    color()
    header(screen)
    footer(screen)
    win = body(screen)
    picked = []
    expanded = []
    parent = Paths(win, root, hidden, picked)
    parent.expand()
    curline = 0
    action = None

    while True:
        # to reset or toggle view of dotfiles we need to create a new Path
        # object before erasing the screen & descending into draw function.
        if action == 'reset':
            picked = []
            expanded = []
            parent = Paths(win, root, hidden, picked)
            parent.expand()
            action = None
        elif action == 'toggle_hidden':
            if hidden:
                hidden = False
            else:
                hidden = True
            parent = Paths(win, root, hidden, picked)
            parent.expand()
            action = None
            # restore expanded & marked state
            for child, depth in parent.traverse():
                if child.name in expanded:
                    child.expand()
                if child.name in picked:
                    child.marked = True

        win.erase()  # https://stackoverflow.com/a/24966639 - prevent flashes

        picked, expanded, line, curline = draw(
            parent, action, curline, picked, expanded)

        win.refresh()

        action, curline = parse(win, curline, line)

        if action == 'quit':
            return picked
