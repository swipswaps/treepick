# Copyright (c) 2018, Toby Slight. All rights reserved.
# ISC License (ISCL) - see LICENSE file for details.

import os
import curses
import fnmatch

from pdu import du
from .screen import Screen


class Paths(Screen):
    def __init__(self, screen, name, hidden, curline=0,
                 picked=[], expanded=set(), sized=dict()):
        Screen.__init__(self, screen, picked)
        self.name = name
        self.hidden = hidden
        self.picked = picked
        self.expanded = expanded
        self.sized = sized
        self.paths = None
        self.marked = False
        self.children = self.getchildren()
        self.lastpath, self.lasthidden = (None,)*2
        self.curline = curline

    ###########################################################################
    #                          SHOW OR HIDE DOTFILES                          #
    ###########################################################################

    def toggle_hidden(self):
        self.paths = None

        if self.hidden:
            # keep two copies of record so we can restore from state when
            # re-hiding
            self.lastpath = self.children[self.curline]
            self.hidden = False
        else:
            # keep two copies of record so we can restore from state
            self.lasthidden = self.children[self.curline]
            self.hidden = True

        self.drawtree()

        if self.lasthidden in self.children:
            self.curline = self.children.index(self.lasthidden)
        elif self.lastpath in self.children:
            self.curline = self.children.index(self.lastpath)

    ###########################################################################
    #                       EXPAND AND COLLAPSE METHODS                       #
    ###########################################################################

    def expand(self, recurse=False, toggle=False):
        if os.path.isdir(self.name) and self.children and recurse:
            self.expanded.add(self.name)
            for c, d in self.traverse():
                if d < 2 and os.path.isdir(c.name) and c.children:
                    self.expanded.add(c.name)
            self.curline += 1
        elif os.path.isdir(self.name) and self.children:
            if toggle:
                if self.name in self.expanded:
                    self.expanded.remove(self.name)
                else:
                    self.expanded.add(self.name)
            else:
                self.expanded.add(self.name)
                self.curline += 1

    def collapse(self, depth, recurse=False):
        if depth > 1 and recurse:
            p = self.prevparent(depth)
            self.expanded.remove(p)
            for x in list(self.expanded):  # iterate over copy
                par = os.path.abspath(p)
                path = os.path.abspath(x)
                if path.startswith(par):
                    self.expanded.remove(x)
        elif self.name in self.expanded:
            self.expanded.remove(self.name)
        elif depth > 1 and not os.path.isdir(self.name):
            p = self.prevparent(depth)
            self.expanded.remove(p)

    ###########################################################################
    #                              PICKING NODES                              #
    ###########################################################################

    def pick(self, pickall=False, globs=[]):
        if pickall and not globs:
            for c, d in self.traverse():
                if d == 0:
                    continue
                if c.name in self.picked:
                    self.picked.remove(c.name)
                else:
                    self.picked.append(c.name)
        elif pickall and globs:
            for c, d in self.traverse():
                for g in globs:
                    if (fnmatch.fnmatch(c.name, g) or
                            fnmatch.fnmatch(os.path.basename(c.name), g)):
                        if c.name in self.picked:
                            self.picked.remove(c.name)
                        else:
                            self.picked.append(c.name)
        else:
            if self.name in self.picked:
                self.picked.remove(self.name)
            else:
                self.picked.append(self.name)
            self.curline += 1

    ###########################################################################
    #                           LINE JUMPING METHODS                          #
    ###########################################################################

    def nextparent(self, depth):
        '''
        Add lines to current line by traversing the grandparent object again
        and once we reach our current line counting every line that is prefixed
        with the parent directory.
        '''
        pdir = os.path.dirname(self.name)
        if depth > 1:  # can't jump to parent of root node!
            line = 0
            for c, d in self.traverse():
                if line > self.curline and c.name.startswith(pdir + os.sep):
                    self.curline += 1
                line += 1
        else:  # otherwise just skip to next directory
            line = -1  # skip hidden parent node
            for c, d in self.traverse():
                if line > self.curline:
                    self.curline += 1
                    if os.path.isdir(c.name) and c.name in self.children[0:]:
                        break
                line += 1

    def prevparent(self, depth):
        '''
        Subtract lines from our self.curline if the name of a node is prefixed with
        the parent directory when traversing the grandparent object.
        '''
        pdir = os.path.dirname(self.name)
        if depth > 1:  # can't jump to parent of root node!
            for c, d in self.traverse():
                if c.name == self.name:
                    break
                if c.name.startswith(pdir):
                    self.curline -= 1
        else:  # otherwise jus skip to previous directory
            pdir = self.name
            # - 1 otherwise hidden parent node throws count off & our
            # self.curline doesn't change!
            line = -1
            for c, d in self.traverse():
                if c.name == self.name:
                    break
                if os.path.isdir(c.name) and c.name in self.children[0:]:
                    self.curline = line
                line += 1
        return pdir

    def find(self, string):
        matches = []
        line = -1
        for c, d in self.traverse():
            if string in os.path.basename(c.name):
                matches.append(line)
            line += 1
        if matches:
            self.curline = self.findnext(self.curline, matches)
        return matches

    def findnext(self, matches):
        for m in range(len(matches)):
            if self.curline == matches[len(matches) - 1]:
                return matches[0]
            elif self.curline < matches[m]:
                return matches[m]

    def findprev(self, matches):
        for m in range(len(matches)):
            if self.curline <= matches[m]:
                return matches[m-1]

    ###########################################################################
    #                         SIZE CALCULATING METHODS                        #
    ###########################################################################

    def getsize(self, sizeall=False):
        if sizeall:
            for c, d in self.traverse():
                self.sized[os.path.abspath(c.name)] = None
        else:
            self.sized[os.path.abspath(self.name)] = None
            self.curline += 1

    ###########################################################################
    #                       CURSES LINE DRAWING METHODS                       #
    ###########################################################################

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

    def drawtree(self, action):
        '''
        Loop over the object, process path attribute sets, and drawlines based
        on their current contents.
        '''
        self.win.erase()
        line = 0
        for c, d in self.traverse():
            path = os.path.abspath(c.name)
            if d == 0:
                continue
            if line == self.curline:
                self.color.curline(c.name)
                self.mkheader(c.name)
                self.mkfooter(c.name, c.children)
                if action == 'expand':
                    c.expand()
                elif action == 'expand_all':
                    c.expand(recurse=True)
                elif action == 'toggle_expand':
                    c.expand(toggle=True)
                elif action == 'collapse':
                    c.collapse(depth)
                elif action == 'collapse_all':
                    c.collapse(depth, recurse=True)
                elif action == 'toggle_pick':
                    c.pick()
                elif action == 'pickall':
                    c.pick(pickall=True)
                elif action == 'nextparent':
                    c.nextparent(d)
                elif action == 'prevparent':
                    c.prevparent(d)
                elif action == 'getsize':
                    c.getsize()
                elif action == 'getsizeall':
                    c.getsize(sizeall=True)
                action = None
            else:
                self.color.default(c.name)
            if fnmatch.filter(self.picked, c.name):
                c.marked = True
            if path in self.sized and not self.sized[path]:
                self.sized[path] = " [" + du(c.name) + "]"
            c.drawline(d, line, self.win)
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
