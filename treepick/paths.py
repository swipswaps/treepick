import os
import curses

from .color import Color
from .du import DiskUsage


class Paths:
    def __init__(self, scr, name, hidden, picked):
        self.scr = scr
        self.name = name
        self.hidden = hidden
        self.picked = picked
        self.color = Color(self.scr, self.picked)
        try:
            if self.hidden:
                self.children = sorted(self.listdir(name))
            else:
                self.children = sorted(os.listdir(name))
        except:
            self.children = None  # probably permission denied
        self.paths = None
        self.expanded = False
        self.marked = False
        self.getsize = False
        self.size = None
        self.du = DiskUsage()

    def listdir(self, path):
        for f in os.listdir(path):
            if not f.startswith('.'):
                yield f

    def drawline(self, depth, width):
        pad = ' ' * 4 * depth
        mark = self.mark()
        size = self.hrdu()
        node = self.getnode()
        nodestr = '{}{}{}{}'.format(pad, node, size, mark)
        return nodestr + ' ' * (width - len(nodestr))

    def drawlines(self, depth, curline, line):
        offset = max(0, curline - curses.LINES + 10)
        y = line - offset
        x = 0
        string = self.drawline(depth - 1, curses.COLS)
        if 0 <= line - offset < curses.LINES - 1:
            self.scr.addstr(y, x, string)  # paint str at y, x co-ordinates

    def getnode(self):
        if not os.path.isdir(self.name):
            return '    ' + os.path.basename(self.name)
        elif self.expanded:
            return '[-] ' + os.path.basename(self.name) + '/'
        elif self.getpaths():
            return '[+] ' + os.path.basename(self.name) + '/'
        elif self.children is None:
            return '[?] ' + os.path.basename(self.name) + '/'
        else:
            return '[ ] ' + os.path.basename(self.name) + '/'

    def mark(self):
        if self.marked:
            return ' *'
        else:
            return ''

    def hrdu(self):
        if self.getsize:
            bytes_ = self.du.totalsize(self.name)
            size_ = self.du.convert(bytes_)
            # save state as object attribute
            self.size = " (" + size_ + ")"
            return self.size
        else:
            if self.size:
                return self.size
            else:
                return ''

    def expand(self):
        if os.path.isdir(self.name):
            self.expanded = True
            # self.color.default(self.name)

    def collapse(self):
        if os.path.isdir(self.name):
            self.expanded = False

    def nextparent(self, parent, curline, depth):
        '''
        Get index of current parent directory, in the context of it's traversal,
        count until we reach the node corresponding to that index + 1 - ie) the
        next parent.
        '''
        line = 0
        count = 0
        if depth > 1:
            curpar = os.path.dirname(os.path.dirname(self.name))
            cpaths = Paths(self.scr, curpar, self.hidden, self.picked)
            curdir = os.path.basename(os.path.dirname(self.name))
            curidx = cpaths.children.index(curdir)
            nextdir = cpaths.children[curidx + 1]
            for c, d in parent.traverse():
                if os.path.basename(c.name) == nextdir:
                    break
                if line > curline:
                    self.color.default(self.name)
                    count += 1
                line += 1
        else:
            # if we're in root then skip to next dir
            for c, d in parent.traverse():
                if line > curline + 1:
                    self.color.default(self.name)
                    count += 1
                    if os.path.isdir(c.name):
                        break
                line += 1
        return count

    def prevparent(self, parent, curline, depth):
        '''
        Count lines from top of parent until we reach our current path and then
        return that count so that we can set curline to it.
        '''
        count = 0
        p = os.path.dirname(self.name)
        # once we hit the parent directory, break, and set the
        # curline to the line number we got to.
        if depth > 1:
            for c, d in parent.traverse():
                if c.name == p:
                    count -= 1
                    c.drawlines(d, 0, count)
                    self.color.default(self.name)
                    return count, c
                count += 1
        else:
            curline -= 1
            return curline, self

    def collapse_all(self, parent, curline, depth):
        if depth > 1:
            self.prevparent(parent, curline, depth)[1].collapse()
            self.color.curline(self.name)
            return self.prevparent(parent, curline, depth)[0]
        else:
            return curline

    def getpaths(self):
        '''
        If we have children, use a list comprehension to instantiate new paths
        objects to traverse.
        '''
        if self.children is None:
            return
        if self.paths is None:
            self.paths = [Paths(
                self.scr, os.path.join(self.name, child), self.hidden, self.picked)
                for child in self.children]
        return self.paths

    def traverse(self):
        '''
        Recursive generator that lazily unfolds the filesystem.
        '''
        yield self, 0

        if not self.expanded:
            return

        for child in self.getpaths():
            for c, depth in child.traverse():
                yield c, depth + 1
