# Copyright (c) 2018, Toby Slight. All rights reserved.
# ISC License (ISCL) - see LICENSE file for details.

import os
import curses
import fnmatch

from pdu import du
from .screen import Screen
from .actions import Actions


class Paths(Actions, Screen):
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
        Screen.__init__(self, screen, picked)

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
        return line

    def getnode(self):
        if not os.path.isdir(self.name):
            return '    ' + os.path.basename(self.name)
        elif self.name in self.expanded:
            return '[-] ' + os.path.basename(self.name) + '/'
        elif self.getpaths():
            return '[+] ' + os.path.basename(self.name) + '/'
        elif self.children is None:
            return '[?] ' + os.path.basename(self.name) + '/'
        else:
            return '[ ] ' + os.path.basename(self.name) + '/'

    def mkline(self, depth, width):
        pad = ' ' * 4 * depth
        path = self.getnode()
        node = pad + path
        if os.path.abspath(self.name) in self.sized:
            size = self.sized[os.path.abspath(self.name)]
        else:
            size = ''
        if self.name in self.picked:
            mark = ' *'
        else:
            mark = '  '
        node = node + mark
        sizelen = len(size)
        sizepad = width - sizelen
        nodestr = '{:<{w}}{:>}'.format(node, size, w=sizepad)
        return sizelen, sizepad, nodestr + ' ' * (width - len(nodestr))

    def drawline(self, depth, line, win):
        max_y, max_x = win.getmaxyx()
        offset = max(0, self.curline - max_y + 3)
        y = line - offset
        x = 0
        sizelen, sizepad, string = self.mkline(depth - 1, max_x)
        if 0 <= line - offset < max_y - 1:
            try:
                win.addstr(y, x, string)  # paint str at y, x co-ordinates
                if sizelen > 0 and line != self.curline:
                    win.chgat(y, sizepad, sizelen,
                              curses.A_BOLD | curses.color_pair(5))
            except curses.error:
                pass

    def drawtree(self):
        '''
        Loop over the object, process path attribute sets, and drawlines based
        on their current contents.
        '''
        self.win.erase()
        line = 0
        for child, depth in self.traverse():
            child.curline = self.curline
            if depth == 0:
                continue
            if line == self.curline:
                self.color.curline(child.name)
                self.mkheader(child.name)
                self.mkfooter(child.name, child.children)
            else:
                self.color.default(child.name)
            if fnmatch.filter(self.picked, child.name):
                child.marked = True
            if child.name in self.sized and not self.sized[child.name]:
                self.sized[child.name] = " [" + du(child.name) + "]"
            child.drawline(depth, line, self.win)
            line += 1
        self.win.refresh()
        return line

    ###########################################################################
    #                    PATH OBJECT INSTANTIATION METHODS                    #
    ###########################################################################

    def listdir(self, path):
        '''
        Return a list of all non dotfiles in a given directory.
        '''
        for f in os.listdir(path):
            if not f.startswith('.'):
                yield f

    def getchildren(self):
        '''
        Create list of absolute paths to be used to instantiate path objects
        for traversal, based on whether or not hidden attribute is set.
        '''
        try:
            if self.hidden:
                return [os.path.join(self.name, child)
                        for child in sorted(self.listdir(self.name))]
                # return sorted(self.listdir(self.name))
            else:
                return [os.path.join(self.name, child)
                        for child in sorted(os.listdir(self.name))]
                # return sorted(os.listdir(self.name))
        except OSError:
            return None  # probably permission denied

    def getpaths(self):
        '''
        If we have children, use a list comprehension to instantiate new paths
        objects to traverse.
        '''
        self.children = self.getchildren()
        if self.children is None:
            return
        if self.paths is None:
            self.paths = [Paths(self.screen,
                                os.path.join(self.name, child),
                                self.hidden,
                                self.curline,
                                self.picked,
                                self.expanded,
                                self.sized)
                          for child in self.children]
        return self.paths

    def traverse(self):
        '''
        Recursive generator that lazily unfolds the filesystem.
        '''
        yield self, 0
        if self.name in self.expanded:
            for child in self.getpaths():
                for c, depth in child.traverse():
                    yield c, depth + 1
