import curses
import os


class Color:
    def __init__(self, stdscr, picked):
        self.scr = stdscr
        self.picked = picked
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_YELLOW)

    def getcolors(self):
        curses.start_color()
        curses.use_default_colors()
        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, -1)

    def reset(self):
        self.scr.attrset(curses.color_pair(0))

    def white_blue(self):
        self.scr.attrset(curses.color_pair(1) | curses.A_BOLD)

    def blue_black(self):
        self.scr.attrset(curses.color_pair(2) | curses.A_BOLD)

    def yellow_black(self):
        self.scr.attrset(curses.color_pair(3))

    def black_yellow(self):
        self.scr.attrset(curses.color_pair(4))

    def curline(self, path):
        # can't use "in", as we have to catch all descendants.
        self.white_blue()
        for p in self.picked:
            if path.startswith(p):
                self.black_yellow()

    def default(self, path):
        # can't use "in", as we have to catch all descendants.
        if os.path.isdir(path):
            self.blue_black()
        else:
            self.reset()
        for p in self.picked:
            if path.startswith(p):
                self.yellow_black()
