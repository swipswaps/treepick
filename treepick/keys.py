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
            elif ch == ord('q') or ch == self.ESC:
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
                {
                    'expand': lambda: child.expand(),
                    'expand_all': lambda: child.expand(recurse=True),
                    'toggle_expand': lambda: child.expand(toggle=True),
                    'collapse': lambda: child.collapse(self, depth),
                    'collapse_all': lambda: child.collapse(self, depth, recurse=True),
                    'toggle_pick': lambda: child.pick(),
                    'nextparent': lambda: child.nextparent(self, depth),
                    'prevparent': lambda: child.prevparent(self, depth),
                    'getsize': lambda: child.getsize(),
                }[action]()
            self.curline = child.curline
            line += 1

    def getkeys(self):
        while True:
            self.drawtree()
            key = self.screen.getch()
            keys = {
                ord('q'): self.quit,
                self.ESC: self.quit,
                curses.KEY_F5: self.reset_all,
                ord('R'): self.reset_all,
                curses.KEY_F4: self.reset_picked,
                ord('r'): self.reset_picked,
                ord('.'): self.toggle_hidden,
                curses.KEY_RIGHT: lambda: self.parse_curline('expand'),
                ord('l'): lambda: self.parse_curline('expand'),
                curses.KEY_LEFT: lambda: self.parse_curline('collapse'),
                ord('h'): lambda: self.parse_curline('collapse'),
                curses.KEY_SRIGHT: lambda: self.parse_curline('expand_all'),
                ord('L'): lambda: self.parse_curline('expand_all'),
                curses.KEY_SLEFT: lambda: self.parse_curline('collapse_all'),
                ord('H'): lambda: self.parse_curline('collapse_all'),
                ord('\t'): lambda: self.parse_curline('toggle_expand'),
                ord('\n'): lambda: self.parse_curline('toggle_expand'),
                ord(' '): lambda: self.parse_curline('toggle_pick'),
                ord('v'): lambda: self.pick(pickall=True),
                ord('J'): lambda: self.parse_curline('nextparent'),
                ord('K'): lambda: self.parse_curline('prevparent'),
                ord('s'): lambda: self.parse_curline('getsize'),
                ord('S'): lambda: self.parse_curline('getsizeall'),
                ord('/'): self.find,
                ord('n'): self.findnext,
                ord('N'): self.findprev,
                ord(':'): lambda: self.pick(globs=True),
                curses.KEY_F1: lambda: self.getpadkeys(self.mkkeypad()),
                ord('?'): lambda: self.getpadkeys(self.mkkeypad()),
                curses.KEY_F2: lambda: self.getpadkeys(self.mkpickpad()),
                ord('p'): lambda: self.getpadkeys(self.mkpickpad()),
                curses.KEY_DOWN: self.dn,
                ord('j'): self.dn,
                curses.KEY_UP: self.up,
                ord('k'): self.up,
                curses.KEY_PPAGE: self.pgup,
                ord('b'): self.pgup,
                curses.KEY_NPAGE: self.pgdn,
                ord('f'): self.pgdn,
                curses.KEY_HOME: self.top,
                ord('g'): self.top,
                curses.KEY_END: self.bottom,
                ord('G'): self.bottom,
                curses.KEY_RESIZE: self.resize,
            }
            if keys[key]():
                return self.picked
            self.curline %= self.line
