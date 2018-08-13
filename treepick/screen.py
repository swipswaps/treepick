# Copyright (c) 2018, Toby Slight. All rights reserved.
# ISC License (ISCL) - see LICENSE file for details.

import curses
import getpass
import grp
import os
import pwd
import socket
from .color import Color


class Screen:
    def __init__(self, screen, picked):
        curses.curs_set(0)  # get rid of cursor
        self.screen = screen
        self.y, self.x = self.screen.getmaxyx()
        self.header = curses.newwin(0, self.x, 0, 0)
        self.win = curses.newwin(self.y - 3, self.x, 2, 0)
        self.footer = curses.newwin(0, self.x, self.y - 1, 0)
        self.screen.refresh()
        self.win.refresh()
        self.footer.refresh()
        self.header.refresh()
        self.picked = picked
        self.color = Color(self.win, self.picked)

    def mkheader(self, path):
        # msg = "[hjkl/HJKL] move/jump [SPC/v/:] "
        # msg += "pick/all/glob [s/S] size/all [TAB] expand"
        # startch = [i for i, ltr in enumerate(msg) if ltr == "["]
        # endch = [i for i, ltr in enumerate(msg) if ltr == "]"]
        user = getpass.getuser()
        host = socket.gethostname()
        userhost = user + "@" + host
        msg = userhost + " " + path
        try:
            self.header.addstr(0, 0, msg)
            self.header.clrtoeol()  # more frugal than erase. no flicker.
            self.header.chgat(0, 0, len(userhost),
                              curses.A_BOLD | curses.color_pair(2))
            self.header.chgat(0, len(userhost) + 1,
                              curses.A_BOLD | curses.color_pair(3))
            # for i in range(len(startch)):
            #     self.header.chgat(0, startch[i], endch[i] - startch[i] + 1,
            #                       curses.A_BOLD | curses.color_pair(3))
        except curses.error:
            pass
        self.header.refresh()

    def mkfooter(self, path, children):
        from datetime import datetime
        # msg = "[?] show keys [.] toggle hidden [/] find"
        # msg += " [p] view picks [r] reset [q] quit"
        # startch = [i for i, ltr in enumerate(msg) if ltr == "["]
        # endch = [i for i, ltr in enumerate(msg) if ltr == "]"]
        user = pwd.getpwuid(os.stat(path).st_uid)[0]
        group = grp.getgrgid(os.stat(path).st_gid)[0]
        usergroup = user + " " + group

        mtime = os.path.getmtime(path)
        mdate = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')

        mode = oct(os.stat(path).st_mode)[-3:]

        if children:
            children = len(children)
        else:
            children = ""

        msg = usergroup + " " + mdate + " " + mode + " " + str(children)
        try:
            self.footer.addstr(0, 0, msg)
            self.footer.clrtoeol()  # more frugal than erase. no flicker.
            self.footer.chgat(0, 0, len(usergroup), curses.A_BOLD |
                              curses.color_pair(2))
            self.footer.chgat(0, len(usergroup) + 1, len(mdate),
                              curses.A_BOLD | curses.color_pair(3))
            self.footer.chgat(0, len(usergroup) + len(mdate) + 2, len(mode),
                              curses.A_BOLD | curses.color_pair(6))
            self.footer.chgat(0, len(usergroup) + len(mdate) + len(mode) + 2,
                              curses.A_BOLD | curses.color_pair(5))
            # for i in range(len(startch)):
            #     self.footer.chgat(0, startch[i], endch[i] - startch[i] + 1,
            #                       curses.A_BOLD | curses.color_pair(3))
        except curses.error:
            pass
        self.footer.refresh()

    def showpicks(self):
        self.win.erase()
        self.win.attrset(curses.color_pair(0))
        try:
            if self.picked:
                self.win.chgat(0, 0, curses.color_pair(3) | curses.A_BOLD)
                self.win.addstr(0, 0, "\n".join(self.picked))
                self.win.addstr(len(self.picked) + 1, 0,
                                "Press any key to return.")
                self.win.chgat(len(self.picked) + 1, 0,
                               curses.color_pair(3) | curses.A_BOLD)
            else:
                self.win.addstr(0, 0, "You haven't picked anything yet!")
                self.win.chgat(0, 0, curses.color_pair(1) | curses.A_BOLD)
                self.win.addstr(2, 0, "Press any key to return.")
                self.win.chgat(2, 0, curses.color_pair(3) | curses.A_BOLD)
        except curses.error:
            pass
        self.win.getch()

    def txtbox(self, prompt):
        from curses.textpad import Textbox
        length = len(prompt)
        y, x = self.screen.getmaxyx()
        self.footer.erase()
        self.footer.addstr(prompt)
        self.footer.chgat(0, 0, length, curses.A_BOLD | curses.color_pair(3))
        curses.curs_set(1)
        self.footer.refresh()
        tb = self.footer.subwin(y - 1, length)
        box = Textbox(tb)
        box.edit()
        curses.curs_set(0)
        self.mkfooter()
        return box.gather()

    def resize(self):
        # self.screen.erase()
        self.y, self.x = self.screen.getmaxyx()
        # self.header = curses.newwin(0, self.x, 0, 0)
        # self.win = curses.newwin(self.y - 3, self.x, 2, 0)
        # self.footer = curses.newwin(0, self.x, self.y - 1, 0)
        # self.header.resize(0, self.x)
        # self.header.resize(self.y - self.y - 1, self.x)
        self.win.resize(self.y - 3, self.x)
        self.footer.resize(self.y, self.x)
        self.screen.refresh()
        self.header.refresh()
        self.win.refresh()
        self.footer.refresh()
