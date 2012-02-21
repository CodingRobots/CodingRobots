#!/usr/bin/env python

# Copyright 2009 Lee Harr
#
# This file is part of pybotwar.
#
# Pybotwar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pybotwar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pybotwar.  If not, see <http://www.gnu.org/licenses/>.


import os
import sys
import glob

from PyQt4 import QtCore, QtGui, uic
from PyQt4.Qt import QFrame, QWidget, QHBoxLayout, QPainter

import conf

uidir = 'data/ui'

class CombatantsEditor(QtGui.QMainWindow):
    def __init__(self, parent):
        self.parent = parent
        QtGui.QMainWindow.__init__(self)
        uifile = 'combatants.ui'
        uipath = os.path.join(uidir, uifile)
        CEClass, _ = uic.loadUiType(uipath)
        self.ui = CEClass()
        self.ui.setupUi(self)
        self.show_selected()
        self.show_available()

    def show_available(self):
        available = self.ui.availablerobots
        selected = self.ui.selectedrobots
        robotpaths = set()
        for d in conf.robot_dirs:
            g = '%s/*.py' % d
            found = glob.glob(g)
            if conf.template in found:
                found.remove(conf.template)
            robotpaths.update(found)

        for robotpath in robotpaths:
            d, filename = os.path.split(robotpath)
            robotname = filename[:-3]
            if not available.findItems(robotname, QtCore.Qt.MatchExactly):
                item = QtGui.QListWidgetItem(robotname, available)


    def show_selected(self):
        selected = self.ui.selectedrobots
        for robotname in conf.robots:
            item = QtGui.QListWidgetItem(robotname, selected)

    def addrobot(self):
        available = self.ui.availablerobots
        selected = self.ui.selectedrobots
        for item in available.selectedItems():
            name = str(item.text())
            newitem = QtGui.QListWidgetItem(name, selected)

    def removerobot(self):
        available = self.ui.availablerobots
        selected = self.ui.selectedrobots
        for item in selected.selectedItems():
            name = str(item.text())
            row = selected.row(item)
            selected.takeItem(row)
            found = available.findItems(name, QtCore.Qt.MatchExactly)
            if not found:
                available.addItem(item)

    def removeall(self):
        selected = self.ui.selectedrobots
        while selected.count():
            item = selected.item(0)
            selected.setItemSelected(item, True)
            self.removerobot()

    def savebattle(self):
        robots = self.getselected()
        fdir = QtCore.QString(os.path.abspath(conf.lineups))
        filepath = QtGui.QFileDialog.getSaveFileName(self, 'Save Battle Lineup As', fdir)
        if not filepath:
            return

        lineup = file(filepath, 'w')
        for name in robots:
            lineup.write(name)
            lineup.write('\n')
        lineup.close()

    def loadbattle(self):
        available = self.ui.availablerobots
        fdir = QtCore.QString(os.path.abspath(conf.lineups))
        fp = QtGui.QFileDialog.getOpenFileName(self, 'Open Battle Lineup', fdir)
        if fp:
            self.removeall()
            lineup = file(fp)

            items = []
            not_available = []
            for line in lineup:
                name = line.strip()
                found = available.findItems(name, QtCore.Qt.MatchExactly)
                if not found:
                    not_available.append(name)
                else:
                    item = found[0]
                    items.append(item)

            if not_available:
                text = 'Robot code not found:\n'
                lines = '\n'.join(not_available)
                warn = QtGui.QMessageBox.warning(self, 'Not Found', text+lines)
            else:
                for item in items:
                    available.setItemSelected(item, True)
                    self.addrobot()

    def getselected(self):
        selected = self.ui.selectedrobots
        robots = []
        for i in range(selected.count()):
            item = selected.item(i)
            name = str(item.text())
            robots.append(name)
        return robots

    def startbattle(self):
        robots = self.getselected()
        conf.robots = robots
        self.parent.restart()
        self.parent.paused = True
        self.close()
        self.parent.startBattle()
