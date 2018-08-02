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
    #                           LINE JUMPING METHODS                          #
    ###########################################################################

    def nextparent(self, parent, curline, depth):
        '''
        Get index of current parent directory, in the context of it's traversal,
        count until we reach the node corresponding to that index + 1 - ie) the
        next parent.
        '''
        if depth > 1:
            p = os.path.dirname(self.name)
            pobj = Paths(self.win, p, self.hidden, self.expanded)
            curdir = os.path.basename(self.name)
            curidx = pobj.children.index(curdir)
            curline += len(pobj.children) - curidx
        return curline

    def prevparent(self, parent, curline, depth):
        '''
        Count lines from top of parent until we reach our current path and then
        return that count so that we can set curline to it.
        '''
        p = os.path.dirname(self.name)
        # once we hit the parent directory, break, and set the
        # curline to the line number we got to.
        if depth > 1:
            curline = 0
            for c, d in parent.traverse():
                if c.name == p:
                    curline -= 1
                    c.drawline(d, 0, curline)
                    self.color.default(self.name)
                    p = c
                    break
                curline += 1
        else:
            curline -= 1
            p = self.name
        return curline, p

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
        nodestr = '{}{}{}'.format(pad, node, size)
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
            if d == 0:
                continue
            if l == curline:
                c.color.curline(c.name)
            else:
                c.color.default(c.name)
            if c.name in self.picked:
                c.marked = True
            path = os.path.abspath(c.name)
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
