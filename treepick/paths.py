import os
import curses

from .color import Color
from pdu import du


class Paths:
    def __init__(self, win, name, hidden,
                 picked=set(), expanded=set(), sized=dict()):
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

    def pick(self, curline, parent=None):
        if parent:
            for c, d in parent.traverse():
                if d == 0:
                    continue
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
        Add lines to current line by traversing the grandparent object again
        and once we reach our current line counting every line that is prefixed
        with the parent directory.
        '''
        pdir = os.path.dirname(self.name)
        if depth > 1:  # can't jump to parent of root node!
            line = 0
            for c, d in parent.traverse():
                if line > curline and c.name.startswith(pdir + os.sep):
                    curline += 1
                line += 1
        else:  # otherwise just skip to next directory
            line = 0
            for c, d in parent.traverse():
                if line > curline + 1:
                    curline += 1
                    if os.path.isdir(c.name) and c.name in parent.children:
                        break
                line += 1
        return curline

    def prevparent(self, parent, curline, depth):
        '''
        Subtract lines from our curline if the name of a node is prefixed with
        the parent directory when traversing the grandparent object.
        '''
        pdir = os.path.dirname(self.name)
        if depth > 1:  # can't jump to parent of root node!
            for c, d in parent.traverse():
                if c.name == self.name:
                    break
                if c.name.startswith(pdir):
                    curline -= 1
        else:  # otherwise jus skip to previous directory
            pdir = self.name
            line = 0
            for c, d in parent.traverse():
                if c.name == self.name:
                    break
                if os.path.isdir(c.name) and c.name in parent.children[0:]:
                    curline = line
                line += 1
            curline -= 1
            if curline < 0:
                curline = curses.LINES - 1
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
        Loop over the object, process path attribute sets, and drawlines based
        on their current contents.
        '''
        self.win.erase()
        line = 0
        for c, d in self.traverse():
            path = os.path.abspath(c.name)
            if d == 0:
                continue
            if line == curline:
                c.color.curline(c.name)
            else:
                c.color.default(c.name)
            if c.name in self.picked:
                c.marked = True
            if path in self.sized and not self.sized[path]:
                self.sized[path] = " (" + du(c.name) + ")"
            c.drawline(d, curline, line)
            line += 1
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
        Create list of absolute paths to be used to instantiate path objects for
        traversal, based on whether or not hidden attribute is set.
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
