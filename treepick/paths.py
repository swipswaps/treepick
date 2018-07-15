import curses
import os

from color import Colors
from du import DiskUsage


class Paths:
    def __init__(self, scr, name, hidden, picked):
        self.scr = scr
        self.name = name
        self.hidden = hidden
        self.picked = picked
        self.colors = Colors(self.scr, self.picked)
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
        offset = max(0, curline - curses.LINES + 2)
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
            # self.colors.default(self.name)

    def collapse(self):
        if os.path.isdir(self.name):
            self.expanded = False

    # next & prev parent need a lot of love. multiple bugs!
    def nextparent(self, parent, curline, depth):
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
                    self.colors.default(self.name)
                    count += 1
                line += 1
        else:
            # if we're in root then skip to next dir
            for c, d in parent.traverse():
                if line > curline + 1:
                    self.colors.default(self.name)
                    count += 1
                    if os.path.isdir(c.name):
                        break
                line += 1
        return count

    def prevparent(self, parent):
        '''
        Count lines from top of parent until we reach our current path and then
        return that count so that we can set curline to it.
        '''
        count = 0
        p = os.path.dirname(self.name)
        # once we hit the parent directory, break, and set the
        # curline to the line number we got to.
        for c, d in parent.traverse():
            if c.name == p:
                break
            count += 1
        self.colors.default(self.name)
        return count

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
