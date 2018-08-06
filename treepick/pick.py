import os
import cgitb
import curses
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


def header(screen):
    msg = "Use arrow keys, Vi [h,j,k,l], or Emacs [b,f,p,n] keys to navigate"
    try:
        screen.addstr(msg)
        screen.chgat(0, 19, 9, curses.A_BOLD | curses.color_pair(3))
        screen.chgat(0, 39, 9, curses.A_BOLD | curses.color_pair(3))
    except curses.error:
        pass


def footer(screen, y):
    msg = "[SPC] toggle mark, [?] show all keybindings, [q] to quit."
    try:
        line = y - 1
        screen.addstr(line, 0, msg)
        screen.chgat(line, 0, 5, curses.A_BOLD | curses.color_pair(3))
        screen.chgat(line, 19, 3, curses.A_BOLD | curses.color_pair(3))
        screen.chgat(line, 45, 3, curses.A_BOLD | curses.color_pair(3))
    except curses.error:
        pass


def reset(win, root, hidden):
    parent = Paths(win, root, hidden, expanded=set([root]), sized=dict())
    action = None
    curline = 0
    return parent, action, curline


def init(screen, win=None, resize=False):
    curses.curs_set(0)  # get rid of cursor
    y, x = screen.getmaxyx()
    header(screen)
    footer(screen, y)
    Color(screen)
    if resize:
        win.resize(y - 3, x)
    else:
        win = curses.newwin(y - 3, x, 2, 0)
    screen.refresh()
    win.refresh()
    return win


def pick(screen, root, hidden, relative):
    win = init(screen)
    parent, action, curline = reset(win, root, hidden)
    lasthidden = None
    while True:
        # to reset or toggle view of dotfiles we need to create a new Path
        # object before erasing the screen & descending into process function.
        if action == 'reset':
            parent, action, curline = reset(win, root, hidden)
        elif action == 'toggle_hidden':
            if parent.hidden:
                # keep two copies of record so we can restore from state when
                # re-hiding
                curpath, lastpath = (parent.children[curline],)*2
                # this needs to be reset otherwise we use the old objects
                parent.paths = None
                parent.hidden = False
                parent.drawtree(curline)
                curline = parent.children.index(curpath)
                if lasthidden in parent.children:
                    curline = parent.children.index(lasthidden)
                else:
                    curline = parent.children.index(curpath)
            else:
                # keep two copies of record so we can restore from state
                curpath, lasthidden = (parent.children[curline],)*2
                parent.paths = None
                parent.hidden = True
                parent.drawtree(curline)
                if curpath in parent.children:
                    curline = parent.children.index(curpath)
                else:
                    curline = parent.children.index(lastpath)
            action = None
            continue
        elif action == 'resize':
            screen.erase()
            win.erase()
            init(screen, win=win, resize=True)
        elif action == 'quit':
            if relative:
                return [p[len(root + os.sep):] for p in parent.picked]
            return parent.picked
        curline, line = process(parent, action, curline)
        parent.drawtree(curline)
        action, curline = parse(screen, win, curline, line)
