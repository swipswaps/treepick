import os
import curses

from .color import Color
from pdu import du


class Paths:
    def __init__(self, win, name, hidden, picked=set(), expanded=set(), sized=dict()):
        self.win = win
        self.name = name
        self.hidden = hidden
        self.picked = picked
        self.expanded = expanded
        self.sized = sized
        self.color = Color(self.win, self.picked)
        self.paths = None
        self.marked = False
        self.children = self.getchildren()

    ###########################################################################
    #                       EXPAND AND COLLAPSE METHODS                       #
    ###########################################################################

    def expand(self, curline, recurse=False, toggle=False):
        if os.path.isdir(self.name) and self.children and recurse:
            self.expanded.add(self.name)
            for c, d in self.traverse():
                if d < 2 and os.path.isdir(c.name) and c.children:
                    self.expanded.add(c.name)
            curline += 1
        elif os.path.isdir(self.name) and self.children:
            if toggle:
                if self.name in self.expanded:
                    self.expanded.remove(self.name)
                else:
                    self.expanded.add(self.name)
            else:
                self.expanded.add(self.name)
                curline += 1
        return curline

    def collapse(self, parent, curline, depth, recurse=False):
        if depth > 1 and recurse:
            curline, p = self.prevparent(parent, curline, depth)
            self.expanded.remove(p)
            for x in list(self.expanded):  # iterate over copy
                par = os.path.abspath(p)
                path = os.path.abspath(x)
                if path.startswith(par):
                    self.expanded.remove(x)
        elif self.name in self.expanded:
            self.expanded.remove(self.name)
        return curline

    ###########################################################################
    #                              PICKING NODES                              #
    ###########################################################################

    def pick(self, curline, p=None, pickall=False):
        if pickall:
            for c, d in p.traverse():
                if c.name in self.picked:
                    self.picked.remove(c.name)
                else:
                    self.picked.add(c.name)
        else:
            if self.name in self.picked:
                self.picked.remove(self.name)
            else:
                self.picked.add(self.name)
            curline += 1
        return curline

    ###########################################################################
    #                           LINE JUMPING METHODS                          #
    ###########################################################################

    def nextparent(self, parent, curline, depth):
        '''
        Find index of current path in the context of our parents traversal by
        instantiating an object of the pqrent. Find the size of it's children
        and subtract our index from that, to calculate how many lines we need to
        jump to get to the end of current list or children.
        '''
        pdir = os.path.dirname(self.name)
        pobj = Paths(self.win, pdir, self.hidden)
        if depth > 1:  # can't jump to parent of root node!
            curpath = os.path.basename(self.name)
            curindex = pobj.children.index(curpath)
            curline += len(pobj.children) - curindex
        else:  # otherwise just skip to next directory
            line = 0
            for c, d in parent.traverse():
                if line > curline + 1:
                    curline += 1
                    if os.path.isdir(c.name):
                        break
                    line += 1
        return curline

    def prevparent(self, parent, curline, depth):
        '''
        Use the same method as nextparent to find out current place in child
        directory, then subtract the index of that place from our current line -
        ie) jump to the first element of the parent_path.children list.
        '''
        pdir = os.path.dirname(self.name)
        pobj = Paths(self.win, pdir, self.hidden)
        if depth > 1:  # can't jump to parent of root node!
            curpath = os.path.abspath(self.name)
            for c, d in parent.traverse():
                cpath = os.path.abspath(c.name)
                if cpath == curpath:
                    break
                if cpath.startswith(pdir):
                    curline -= 1
        else:  # otherwise jus skip to previous directory
            pdir = self.name
            line = 0
            for c, d in parent.traverse():
                if line <= curline and os.path.isdir(c.name):
                    lastdir = os.path.basename(c.name)
                    line += 1
            if lastdir != '.':
                curline = parent.children.index(lastdir)
        return curline, pdir

    ###########################################################################
    #                         SIZE CALCULATING METHODS                        #
    ###########################################################################

    def getsize(self, curline, parent, sizeall=False):
        if sizeall:
            for c, d in parent.traverse():
                self.sized[os.path.abspath(c.name)] = None
        else:
            self.sized[os.path.abspath(self.name)] = None
            curline += 1
        return curline

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
        node = self.getnode()
        if os.path.abspath(self.name) in self.sized:
            size = self.sized[os.path.abspath(self.name)]
        else:
            size = ''
        if self.name in self.picked:
            mark = ' *'
        else:
            mark = ''
        nodestr = '{}{}{}{}'.format(pad, node, size, mark)
        return nodestr + ' ' * (width - len(nodestr))

    def drawline(self, depth, curline, line):
        max_y, max_x = self.win.getmaxyx()
        offset = max(0, curline - max_y + 8)
        y = line - offset
        x = 0
        string = self.mkline(depth - 1, max_x)
        if 0 <= line - offset < max_y - 1:
            self.win.addstr(y, x, string)  # paint str at y, x co-ordinates

    def drawtree(self, curline):
        '''
        Loop over the object, process path attribute sets, and drawlines based on
        their current contents.
        '''
        self.win.erase()
        l = 0
        for c, d in self.traverse():
            path = os.path.abspath(c.name)
            if d == 0:
                continue
            if l == curline:
                c.color.curline(c.name)
            else:
                c.color.default(c.name)
            if c.name in self.picked:
                c.marked = True
            if path in self.sized and not self.sized[path]:
                self.sized[path] = " (" + du(c.name) + ")"
            c.drawline(d, curline, l)
            l += 1
        self.win.refresh()

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
        Create list of paths to be used to instantiate path objects for traversal,
        based on whether or not hidden attribute is set.
        '''
        try:
            if self.hidden:
                return sorted(self.listdir(self.name))
            else:
                return sorted(os.listdir(self.name))
        except:
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
            self.paths = [Paths(self.win,
                                os.path.join(self.name, child),
                                self.hidden,
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
