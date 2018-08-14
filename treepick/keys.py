# Copyright (c) 2018, Toby Slight. All rights reserved.
# ISC License (ISCL) - see LICENSE file for details.

import curses
from os import environ
environ.setdefault('ESCDELAY', '12')  # otherwise it takes an age!
ESC = 27


def show(screen):
    from textwrap import dedent
    msg = '''
        UP, k             : Step up one line.
        DOWN, j           : Step down one line.
        K                 : Jump to previous parent directory.
        J                 : Jump to next parent directory.
        PGDN, f           : Jump down a page of lines.
        PGUP, b           : Jump up a page of lines.
        HOME, g           : Jump to first line.
        END, G            : Jump to last line.
        RIGHT, l          : Expand and step into directory.
        TAB, RET          : Toggle expansion/collapse of directory.
        LEFT, h           : Collapse directory.
        SHIFT RIGHT, L    : Expand directory and child directories.
        SHIFT LEFT, H     : Jump to parent directory and collapse all.
        SPC               : Toggle picking of paths.
        v                 : Toggle picking of all currently expanded paths.
        :                 : Toggle picking of paths based on entered globs.
        p                 : View a list of all picked paths.
        /                 : Search for an entered string.
        n                 : Jump to next occurrence of last search string.
        N                 : Jump to previous occurrence of last search string.
        .                 : Toggle display of dotfiles.
        s                 : Display total size of path, recursively
        S                 : Display totol size of all currently expanded paths.
        F5, r             : Reset marking and expansion.
        F1, ?             : View this help page.
        q, ESC            : Quit and display all marked paths.
        '''
    msg = dedent(msg).strip()
    lc = len(msg.splitlines())
    footstr = "[j,k,f,b] or [DOWN, UP, PGUP, PGDN] to scroll."
    footstr += " [q] or [ESC] to return."
    startch = [i for i, ltr in enumerate(footstr) if ltr == "["]
    endch = [i for i, ltr in enumerate(footstr) if ltr == "]"]

    screen.erase()

    keypad = curses.newpad(lc, curses.COLS)
    footer = curses.newwin(0, curses.COLS, curses.LINES - 1, 0)

    try:
        keypad.addstr(0, 0, msg)
        keypad.scrollok(1)
        keypad.idlok(1)
        footer.addstr(0, 0, footstr)
        for i in range(len(startch)):
            footer.chgat(0, startch[i], endch[i] - startch[i] + 1,
                         curses.A_BOLD | curses.color_pair(3))
    except curses.error:
        pass

    screen.refresh()
    footer.refresh()

    pos = 0
    keypad.refresh(pos, 0, 0, 0, curses.LINES - 2, curses.COLS - 1)

    while True:
        ch = screen.getch()
        if (ch == curses.KEY_DOWN or ch == ord('j')):
            if pos < lc - curses.LINES:
                pos += 1
        elif (ch == curses.KEY_UP or ch == ord('k')):
            if pos > 0:
                pos -= 1
        elif (ch == curses.KEY_NPAGE or ch == ord('f')):
            pos += curses.LINES - 1
            if pos >= lc - curses.LINES:
                pos = lc - curses.LINES
        elif (ch == curses.KEY_PPAGE or ch == ord('b')):
            pos -= curses.LINES - 1
            if pos < 0:
                pos = 0
        elif ch == ord('q') or ch == ESC:
            break
        keypad.refresh(pos, 0, 0, 0, curses.LINES - 2, curses.COLS - 1)

    screen.erase()
    screen.refresh()


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
    elif ch == curses.KEY_RIGHT or ch == ord('l'):
        action = 'expand'
    elif ch == curses.KEY_LEFT or ch == ord('h'):
        action = 'collapse'
    elif ch == curses.KEY_SRIGHT or ch == ord('L'):
        action = 'expand_all'
    elif ch == curses.KEY_SLEFT or ch == ord('H'):
        action = 'collapse_all'
    elif ch == ord('\t') or ch == ord('\n'):
        action = 'toggle_expand'
    elif ch == ord(' '):
        action = 'toggle_pick'
    elif ch == ord('v'):
        action = 'pickall'
    elif ch == ord('J'):
        action = 'nextparent'
    elif ch == ord('K'):
        action = 'prevparent'
    elif ch == ord('s'):
        action = 'getsize'
    elif ch == ord('S'):
        action = 'getsizeall'
    elif ch == ord('/'):
        action = 'find'
    elif ch == ord('n'):
        action = 'findnext'
    elif ch == ord('N'):
        action = 'findprev'
    elif ch == ord(':'):
        action = 'match'
    elif ch == curses.KEY_F1 or ch == ord('?'):
        show(screen)
    elif ch == curses.KEY_F2 or ch == ord('p'):
        action = 'showpicks'
    elif ch == curses.KEY_DOWN or ch == ord('j'):
        curline += 1
    elif ch == curses.KEY_UP or ch == ord('k'):
        curline -= 1
    elif ch == curses.KEY_PPAGE or ch == ord('b'):
        curline -= max_y
        if curline < 0:
            curline = 0
    elif ch == curses.KEY_NPAGE or ch == ord('f'):
        curline += max_y
        if curline >= line:
            curline = line - 1
    elif ch == curses.KEY_HOME or ch == ord('g'):
        curline = 0
    elif ch == curses.KEY_END or ch == ord('G'):
        curline = line - 1
    elif ch == ord('z'):
        action = 'recenter'
    elif ch == curses.KEY_RESIZE:
        action = 'resize'
    curline %= line
    return action, curline
