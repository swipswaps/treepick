# Copyright (c) 2018, Toby Slight. All rights reserved.
# ISC License (ISCL) - see LICENSE file for details.

import curses
from .screen import Screen
from os import environ
environ.setdefault('ESCDELAY', '12')  # otherwise it takes an age!


class Keys(Screen):
    def __init__(self, screen, picked):
        Screen.__init__(self, screen, picked)
        self.ESC = 27

    def getpadkeys(self, lc):
        self.screen.refresh()
        pos = 0
        self.pad.refresh(pos, 0, 0, 0, self.y - 2, self.x - 1)
        while True:
            ch = self.screen.getch()
            if (ch == curses.KEY_DOWN or ch == ord('j')):
                if pos < lc - self.y + 1:
                    pos += 1
            elif (ch == curses.KEY_UP or ch == ord('k')):
                if pos > 0:
                    pos -= 1
            elif (ch == curses.KEY_NPAGE or ch == ord('f')):
                pos += self.y - 1
                if pos >= lc - self.y + 1:
                    pos = lc - self.y + 1
            elif (ch == curses.KEY_PPAGE or ch == ord('b')):
                pos -= self.y - 1
                if pos < 0:
                    pos = 0
            elif (ch == curses.KEY_RESIZE):
                self.resize(lc)
            elif ch == ord('q') or ch == 27:
                break
            self.pad.refresh(pos, 0, 0, 0, self.y - 2, self.x - 1)
        self.screen.erase()
        self.screen.refresh()

    def getkeys(self, curline, line):
        action = None
        max_y, max_x = self.win.getmaxyx()
        ch = self.screen.getch()
        if ch == ord('q') or ch == self.ESC:
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
            lc = self.mkkeypad()
            self.getpadkeys(lc)
        elif ch == curses.KEY_F2 or ch == ord('p'):
            lc = self.mkpickpad()
            self.getpadkeys(lc)
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
