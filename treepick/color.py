import curses
import os


class Color:
    def __init__(self, stdscr, picked=set()):
        self.scr = stdscr
        self.picked = picked
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_RED, curses.COLOR_WHITE)
        curses.init_pair(8, curses.COLOR_GREEN, curses.COLOR_WHITE)
        curses.init_pair(9, curses.COLOR_YELLOW, curses.COLOR_WHITE)
        curses.init_pair(10, curses.COLOR_BLUE, curses.COLOR_WHITE)
        curses.init_pair(11, curses.COLOR_MAGENTA, curses.COLOR_WHITE)
        curses.init_pair(12, curses.COLOR_CYAN, curses.COLOR_WHITE)

    def reset(self):
        self.scr.attrset(curses.color_pair(0))

    def white_blue(self):
        self.scr.attrset(curses.color_pair(
            10) | curses.A_BOLD | curses.A_REVERSE)

    def blue_black(self):
        self.scr.attrset(curses.color_pair(4) | curses.A_BOLD)

    def yellow_black(self):
        self.scr.attrset(curses.color_pair(3))

    def black_yellow(self):
        self.scr.attrset(curses.color_pair(3) | curses.A_REVERSE)

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
