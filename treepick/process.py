# Copyright (c) 2018, Toby Slight. All rights reserved.
# ISC License (ISCL) - see LICENSE file for details.

from .actions import Actions


class Process(Actions):
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

    def process_parent(self):
        if self.action == 'resize':
            self.resize()
        elif self.action == 'toggle_hidden':
            self.toggle_hidden()
        elif self.action == 'match':
            self.globs = self.mktbfooter("Pick: ").strip().split()
            if self.globs:
                self.pick()
        elif self.action == 'find':
            string = self.mktbfooter("Find: ").strip()
            if string:
                self.find(string)
        elif self.action == 'findnext':
            self.findnext()
        elif self.action == 'findprev':
            self.findprev()
        elif self.action == 'getsizeall':
            self.getsize(sizeall=True)
        elif self.action == 'pickall':
            self.pick(pickall=True)

    def process_curline(self):
        line = 0
        for child, depth in self.traverse():
            child.curline = self.curline
            if depth == 0:
                continue
            if line == self.curline:
                if self.action == 'expand':
                    child.expand()
                elif self.action == 'expand_all':
                    child.expand(recurse=True)
                elif self.action == 'toggle_expand':
                    child.expand(toggle=True)
                elif self.action == 'collapse':
                    child.collapse(depth)
                elif self.action == 'collapse_all':
                    child.collapse(self, depth, recurse=True)
                elif self.action == 'toggle_pick':
                    child.pick()
                elif self.action == 'nextparent':
                    child.nextparent(self, depth)
                elif self.action == 'prevparent':
                    child.prevparent(self, depth)
                elif self.action == 'getsize':
                    child.getsize()
                self.action = None
            self.curline = child.curline
            line += 1
