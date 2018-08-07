import curses
from os import environ
environ.setdefault('ESCDELAY', '12')  # otherwise it takes an age!
ESC = 27


def show(win):
    from textwrap import dedent
    msg = '''
        UP, k, p          : Step up one line.
        DOWN, j, n        : Step down one line.
        K, P              : Jump to previous parent directory.
        J, N              : Jump to next parent directory.
        PGDN, d, v        : Jump down a page of lines.
        PGUP, u, V        : Jump up a page of lines.
        g, <              : Jump to first line.
        G, >              : Jump to last line.
        RIGHT, l, f       : Expand and step into directory.
        TAB, RET          : Toggle expansion/collapse of directory.
        LEFT, h, b        : Collapse directory.
        SHIFT RIGHT, L, F : Expand directory and child directories.
        SHIFT LEFT, H, B  : Jump to parent directory and collapse all.
        m, SPC            : Toggle marking of paths.
        M                 : Toggle marking of all currently expanded paths.
        F2, i             : View a list of all marked paths.
        .                 : Toggle display of dotfiles.
        s                 : Display total size of path, recursively
        S                 : Display totol size of all currently expanded paths.
        r                 : Reset marking and expansion.
        F1, ?             : View this help page.
        q, ESC            : Quit and display all marked paths.
        '''
    msg = dedent(msg).strip()
    lc = len(msg.splitlines())
    win.erase()
    win.attrset(curses.color_pair(0))
    try:
        win.addstr(0, 0, msg)
        win.addstr(lc + 1, 0, "Press any key to return.")
        win.chgat(lc + 1, 0, curses.color_pair(3) | curses.A_BOLD)
    except curses.error:
        pass
    win.getch()


def parse(screen, win, curline, line):
    action = None
    max_y, max_x = win.getmaxyx()
    ch = screen.getch()
    if ch == ord('q') or ch == ESC:
        action = 'quit'
    elif ch == curses.KEY_F5 or ch == ord('r'):
        action = 'reset'
    elif ch == ord('.'):
        action = 'toggle_hidden'
    elif ch == curses.KEY_RIGHT or ch == ord('l') or ch == ord('f'):
        action = 'expand'
    elif ch == curses.KEY_LEFT or ch == ord('h') or ch == ord('b'):
        action = 'collapse'
    elif ch == curses.KEY_SRIGHT or ch == ord('L') or ch == ord('F'):
        action = 'expand_all'
    elif ch == curses.KEY_SLEFT or ch == ord('H') or ch == ord('B'):
        action = 'collapse_all'
    elif ch == ord('\t') or ch == ord('\n'):
        action = 'toggle_expand'
    elif ch == ord('m') or ch == ord(' '):
        action = 'toggle_pick'
    elif ch == ord('M'):
        action = 'pickall'
    elif ch == ord('J') or ch == ord('N'):
        action = 'nextparent'
    elif ch == ord('K') or ch == ord('P'):
        action = 'prevparent'
    elif ch == ord('s'):
        action = 'getsize'
    elif ch == ord('S'):
        action = 'getsizeall'
    elif ch == curses.KEY_F1 or ch == ord('?'):
        show(win)
    elif ch == curses.KEY_F2 or ch == ord('i'):
        action = 'showpicks'
    elif ch == curses.KEY_DOWN or ch == ord('j') or ch == ord('n'):
        curline += 1
    elif ch == curses.KEY_UP or ch == ord('k') or ch == ord('p'):
        curline -= 1
    elif ch == curses.KEY_PPAGE or ch == ord('u') or ch == ord('V'):
        curline -= max_y
        if curline < 0:
            curline = 0
    elif ch == curses.KEY_NPAGE or ch == ord('d') or ch == ord('v'):
        curline += max_y
        if curline >= line:
            curline = line - 1
    elif ch == curses.KEY_HOME or ch == ord('g') or ch == ord('<'):
        curline = 0
    elif ch == curses.KEY_END or ch == ord('G') or ch == ord('>'):
        curline = line - 1
    elif ch == curses.KEY_RESIZE:
        action = 'resize'
    curline %= line
    return action, curline
