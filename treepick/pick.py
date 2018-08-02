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
            elif action == 'toggle_mark':
                if child.name in child.picked:
                    child.picked.remove(child.name)
                else:
                    child.picked.add(child.name)
                curline += 1
            elif action == 'next_parent':
                curline = child.nextparent(parent, curline, depth)
            elif action == 'prev_parent':
                curline = child.prevparent(parent, curline, depth)[0]
            elif action == 'get_size':
                child.sized[os.path.abspath(child.name)] = None
                curline += 1
            elif action == 'get_size_all':
                for c, d in parent.traverse():
                    child.sized[os.path.abspath(c.name)] = None
            action = None  # reset action
        line += 1  # keep scrolling!
    return curline, line


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


def reset(win, root, hidden):
    parent = Paths(win, root, hidden, expanded=set(root), sized=dict())
    action = None
    curline = 0
    return parent, action, curline


def init(screen):
    curses.curs_set(0)  # get rid of cursor
    header(screen)
    footer(screen)


def pick(screen, root, hidden):
    init(screen)
    Color(screen)
    win = curses.newwin(curses.LINES - 3, curses.COLS, 2, 0)
    parent, action, curline = reset(win, root, hidden)
    screen.refresh()
    while True:
        # to reset or toggle view of dotfiles we need to create a new Path
        # object before erasing the screen & descending into process function.
        if action == 'reset':
            parent, action, curline = reset(win, root, hidden)
        elif action == 'toggle_hidden':
            if parent.hidden:
                parent.paths = None  # this needs to be reset otherwise we use the old objects
                parent.hidden = False
            else:
                parent.paths = None
                parent.hidden = True
        elif action == 'quit':
            return parent.picked
        curline, line = process(parent, action, curline)
        parent.drawtree(curline)
        action, curline = parse(screen, win, curline, line)
