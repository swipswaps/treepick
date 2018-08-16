# Copyright (c) 2018, Toby Slight. All rights reserved.
# ISC License (ISCL) - see LICENSE file for details.

import curses
from .actions import Actions
from os import environ
environ.setdefault('ESCDELAY', '12')  # otherwise it takes an age!


class Keys(Actions):
    def __init__(self,
                 screen,
                 name,
                 hidden,
                 curline=0,
                 picked=[],
                 expanded=set(),
                 sized=dict()):
        Actions.__init__(self,
                         screen,
                         name,
                         hidden,
                         curline,
                         picked,
                         expanded,
                         sized)
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

    def getkeys(self):
        max_y, max_x = self.win.getmaxyx()
        ch = self.screen.getch()
        if ch == ord('q') or ch == self.ESC:
            self.action = 'quit'
        elif ch == curses.KEY_F5 or ch == ord('r'):
            self.action = 'reset'
        elif ch == ord('.'):
            self.action = 'toggle_hidden'
        elif ch == curses.KEY_RIGHT or ch == ord('l'):
            self.action = 'expand'
        elif ch == curses.KEY_LEFT or ch == ord('h'):
            self.action = 'collapse'
        elif ch == curses.KEY_SRIGHT or ch == ord('L'):
            self.action = 'expand_all'
        elif ch == curses.KEY_SLEFT or ch == ord('H'):
            self.action = 'collapse_all'
        elif ch == ord('\t') or ch == ord('\n'):
            self.action = 'toggle_expand'
        elif ch == ord(' '):
            self.action = 'toggle_pick'
        elif ch == ord('v'):
            self.action = 'pickall'
        elif ch == ord('J'):
            self.action = 'nextparent'
        elif ch == ord('K'):
            self.action = 'prevparent'
        elif ch == ord('s'):
            self.action = 'getsize'
        elif ch == ord('S'):
            self.action = 'getsizeall'
        elif ch == ord('/'):
            self.action = 'find'
        elif ch == ord('n'):
            self.action = 'findnext'
        elif ch == ord('N'):
            self.action = 'findprev'
        elif ch == ord(':'):
            self.action = 'match'
        elif ch == curses.KEY_F1 or ch == ord('?'):
            lc = self.mkkeypad()
            self.getpadkeys(lc)
        elif ch == curses.KEY_F2 or ch == ord('p'):
            lc = self.mkpickpad()
            self.getpadkeys(lc)
        elif ch == curses.KEY_DOWN or ch == ord('j'):
            self.curline += 1
        elif ch == curses.KEY_UP or ch == ord('k'):
            self.curline -= 1
        elif ch == curses.KEY_PPAGE or ch == ord('b'):
            self.curline -= max_y
            if self.curline < 0:
                self.curline = 0
        elif ch == curses.KEY_NPAGE or ch == ord('f'):
            self.curline += max_y
            if self.curline >= self.line:
                self.curline = self.line - 1
        elif ch == curses.KEY_HOME or ch == ord('g'):
            self.curline = 0
        elif ch == curses.KEY_END or ch == ord('G'):
            self.curline = self.line - 1
        elif ch == ord('z'):
            self.action = 'recenter'
        elif ch == curses.KEY_RESIZE:
            self.action = 'resize'
        self.curline %= self.line
