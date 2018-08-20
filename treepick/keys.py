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
                 picked=[],
                 expanded=set(),
                 sized=dict()):
        Actions.__init__(self,
                         screen,
                         name,
                         hidden,
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

    def parse_curline(self, action):
        line = 0
        for child, depth in self.traverse():
            child.curline = self.curline
            if depth == 0:
                continue
            if line == self.curline:
                if action == 'expand':
                    child.expand()
                elif action == 'expand_all':
                    child.expand(recurse=True)
                elif action == 'toggle_expand':
                    child.expand(toggle=True)
                elif action == 'collapse':
                    child.collapse(self, depth)
                elif action == 'collapse_all':
                    child.collapse(self, depth, recurse=True)
                elif action == 'toggle_pick':
                    child.pick()
                elif action == 'nextparent':
                    child.nextparent(self, depth)
                elif action == 'prevparent':
                    child.prevparent(self, depth)
                elif action == 'getsize':
                    child.getsize()
                action = None
            self.curline = child.curline
            line += 1

    def getkeys(self):
        while True:
            max_y, max_x = self.win.getmaxyx()
            self.drawtree()
            ch = self.screen.getch()
            if ch == ord('q') or ch == self.ESC:
                return self.picked
            elif ch == curses.KEY_F5 or ch == ord('R'):
                self.curline = 0
                self.picked = []
                self.expanded = set([self.name])
                self.sized = {}
            elif ch == ord('r'):
                self.picked = []
            elif ch == ord('.'):
                self.toggle_hidden()
            elif ch == curses.KEY_RIGHT or ch == ord('l'):
                self.parse_curline('expand')
            elif ch == curses.KEY_LEFT or ch == ord('h'):
                self.parse_curline('collapse')
            elif ch == curses.KEY_SRIGHT or ch == ord('L'):
                self.parse_curline('expand_all')
            elif ch == curses.KEY_SLEFT or ch == ord('H'):
                self.parse_curline('collapse_all')
            elif ch == ord('\t') or ch == ord('\n'):
                self.parse_curline('toggle_expand')
            elif ch == ord(' '):
                self.parse_curline('toggle_pick')
            elif ch == ord('v'):
                self.pick(pickall=True)
            elif ch == ord('J'):
                self.parse_curline('nextparent')
            elif ch == ord('K'):
                self.parse_curline('prevparent')
            elif ch == ord('s'):
                self.parse_curline('getsize')
            elif ch == ord('S'):
                self.parse_curline('getsizeall')
            elif ch == ord('/'):
                string = self.mktb("Find: ").strip()
                if string:
                    self.find(string)
            elif ch == ord('n'):
                self.findnext()
            elif ch == ord('N'):
                self.findprev()
            elif ch == ord(':'):
                self.globs = self.mktb("Pick: ").strip().split()
                if self.globs:
                    self.pick()
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
            elif ch == curses.KEY_RESIZE:
                self.resize()
            self.curline %= self.line
