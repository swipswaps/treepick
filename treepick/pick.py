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
                if os.path.isdir(child.name):
                    child.expanded.add(child.name)
                curline += 1
            elif action == 'collapse':
                if child.name in child.expanded:
                    child.expanded.remove(child.name)
            elif action == 'expand_all':
                for c, d in child.traverse():
                    # only expand one level at a time
                    if d > 1:
                        continue
                    if os.path.isdir(c.name):
                        child.expanded.add(c.name)
                curline += 1
            elif action == 'collapse_all':
                if depth > 1:
                    curline, p = child.prevparent(parent, curline, depth)
                    if os.path.isdir(p.name):
                        child.expanded.remove(p.name)
            elif action == 'toggle_expand':
                if child.name in child.expanded:
                    child.expanded.remove(child.name)
                elif os.path.isdir(child.name):
                    child.expanded.add(child.name)
                else:
                    curline += 1
            elif action == 'toggle_mark':
                if child.name in child.picked:
                    child.picked.remove(child.name)
                else:
                    child.picked.add(child.name)
                curline += 1
            elif action == 'next_parent':
                curline += child.nextparent(parent, curline, depth)
            elif action == 'prev_parent':
                curline = child.prevparent(parent, curline, depth)[0]
            elif action == 'get_size':
                child.sized.add(child.name)
                curline += 1
            elif action == 'get_size_all':
                for c, d in parent.traverse():
                    child.sized.add(c.name)
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
    parent = Paths(win, root, hidden, expanded=set(root))
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
    screen.refresh()
    parent, action, curline = reset(win, root, hidden)
    while True:
        # to reset or toggle view of dotfiles we need to create a new Path
        # object before erasing the screen & descending into process function.
        if action == 'reset':
            parent, action, curline = reset(win, root, hidden)
        elif action == 'toggle_hidden':
            if parent.hidden:
                hidden = False
                parent = Paths(win, root, hidden, parent.picked,
                               parent.expanded, parent.sized)
            else:
                hidden = True
                parent = Paths(win, root, hidden, parent.picked,
                               parent.expanded, parent.sized)
            action = None
        elif action == 'quit':
            return parent.picked
        curline, line = process(parent, action, curline)
        parent.drawtree(curline)
        action, curline = parse(win, curline, line)
