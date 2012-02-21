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
import math
pi = math.pi
from PyQt4 import QtCore, QtGui, QtSvg, uic
from editor import TextEditor
from combatants import CombatantsEditor

import stats
import conf


def getrend(app):
    filename = 'robot.svg'
    filepath = os.path.join('data/images', filename)
    fp = QtCore.QString(filepath)
    rend = QtSvg.QSvgRenderer(fp, app)
    return rend

uidir = 'data/ui'
uifile = 'mainwindow.ui'
uipath = os.path.join(uidir, uifile)
MWClass, _ = uic.loadUiType(uipath)


class MainWindow(QtGui.QMainWindow):
    def __init__(self, app):
        self.app = app
        self.paused = False

        QtGui.QMainWindow.__init__(self)
        self.ui = MWClass()
        self.ui.setupUi(self)

        self.scene = Scene()
        view = self.ui.arenaview
        view.setScene(self.scene)
        self.scene.view = view
        view.show()

        self.start_game()

        self.singleStep()

        self.ticktimer = self.startTimer(17)

        self.editors = []
        self._fdir = None

        # Call resize a bit later or else view will not resize properly
        self._initialresize = True
        QtCore.QTimer.singleShot(1, self.resizeEvent)

    def start_game(self):
        import game

        self.game = game.Game()
        self.game.w.v.scene = self.scene
        self.game.w.v.app = self.app
        self.game.w.v.rinfo = self.ui.rinfo
        self.game.w.v.setrend()
        self.game.load_robots()

        self.ui.countdown.display(conf.maxtime)

    def closeEvent(self, ev=None):
        self.killTimer(self.ticktimer)

        if len(self.game.procs) > 0:
            self.game.finish()
            stats.dbclose()

        doquit = True
        # Try to close any open editor windows
        for te in self.editors:
            if te.isVisible():
                te.close()

        # If any are still open, don't quit
        for te in self.editors:
            if te.isVisible():
                doquit = False

        if doquit:
            QtGui.qApp.quit()

    def startBattle(self):
        if self.paused:
            self.pauseBattle(False)

    def pauseBattle(self, ev):
        self.paused = ev
        if self.paused:
            self.ui.actionPause.setChecked(True)
            self.ui.actionStart_battle.setDisabled(False)
        else:
            self.ui.actionPause.setChecked(False)
            self.ui.actionStart_battle.setDisabled(True)

    def singleStep(self):
        self.pauseBattle(True)
        self.game.tick()

    def timerEvent(self, ev):
        if not self.paused:
            self.game.tick()
            if not self.game.rnd%60:
                self.ui.countdown.display(self.ui.countdown.value()-1)

        if self.game.rnd > 60 * conf.maxtime:
            self.closeEvent()

        if len(self.game.procs) <= 1:
            self.closeEvent()

    def test(self):
        self.scene.r.set_rotation(self.rot)
        self.scene.r.set_position(self.pos)
        self.scene.r.set_turr_rot(self.turr_rot)

        self.rot += 1
        x, y = self.pos
        self.pos = x-2, y+1

        self.turr_rot -= 2

    def resizeEvent(self, ev=None):
        if self._initialresize:
            # Initial scaling comes out wrong for some reason. Fake it.
            scale = 0.66725
            self._initialresize = False
        else:
            frect = self.ui.arenaframe.frameRect()
            sx, sy = frect.width(), frect.height()
            minsize = min((sx, sy))
            scale = 0.85*(minsize/600.)

        trans = QtGui.QTransform()
        trans.scale(scale, scale)
        self.scene.view.setTransform(trans)

    def notImplementedYet(self):
        self.niy = NotImplementedYet()
        self.niy.show()

    def configure(self):
        cd = TextEditor(self)
        self.editors.append(cd)
        cd.openfile('conf.py')
        cd.show()

    def loadRobot(self, efdir=None):
        if efdir is not None:
            fdir = efdir
        elif self._fdir is None:
            fdir = QtCore.QString(os.path.abspath(conf.robot_dirs[0]))
        else:
            fdir = self._fdir

        fp = QtGui.QFileDialog.getOpenFileName(self, 'Open file', fdir, 'Text files (*.py)')
        if fp:
            # Check to see if the file is already open in an editor
            for ed in self.editors:
                if ed._filepath == fp:
                    # If it is, raise the window and get out
                    ed.activateWindow()
                    ed.raise_()
                    return

            te = TextEditor(self)
            self.editors.append(te)
            te.openfile(fp)
            te.show()

        if efdir is None:
            # Opening from Main Window. Remember directory.
            self._fdir = te._fdir

    def newRobot(self):
        te = TextEditor(self)
        self.editors.append(te)
        te.openfile() # Open the template for a new robot
        te.show()

    def newBattle(self):
        self.com = CombatantsEditor(self)
        self.com.show()

    def newTournament(self):
        self.notImplementedYet()

    def deleteLayoutItems(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.deleteLayoutItems(item.layout())

    def restart(self):
        rinfo = self.ui.rinfo

        for name, robot in self.game.w.robots.items():
            robot.v.kill()

        self.game.finish()
        import world
        world.Robot.nrobots = 0
        Robot.nrobots = 0

        self.scene.removeItem(self.scene.arenarect)
        self.deleteLayoutItems(rinfo)

        self.scene.add_arenarect()
        self.start_game()

        paused = self.paused
        self.singleStep()
        self.pauseBattle(paused)

    def help(self):
        QtGui.QDesktopServices().openUrl(QtCore.QUrl(conf.help_url))

    def about(self):
        AboutDialog().exec_()


class NotImplementedYet(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        uifile = 'bd.ui'
        uipath = os.path.join(uidir, uifile)
        uic.loadUi(uipath, self)

    def accept(self):
        QtGui.QDialog.accept(self)

    def reject(self):
        QtGui.QDialog.reject(self)


class AboutDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        uifile = 'about.ui'
        uipath = os.path.join(uidir, uifile)
        uic.loadUi(uipath, self)


class Scene(QtGui.QGraphicsScene):
    def __init__(self):
        QtGui.QGraphicsScene.__init__(self)
        self.setSceneRect(-350, -350, 700, 700)
        color = QtGui.QColor(30, 30, 60)
        brush = QtGui.QBrush(color)
        self.setBackgroundBrush(brush)
        self.add_arenarect()

    def add_arenarect(self):
        linecolor = QtGui.QColor(90, 90, 70)
        pen = QtGui.QPen(linecolor)
        pen.setWidth(30)
        pen.setJoinStyle(2)
        ar = self.addRect(-300, -300, 600, 600)
        ar.setPen(pen)
        bgcolor = QtGui.QColor(40, 40, 70)
        ar.setBrush(bgcolor)
        self.arenarect = ar


size = 30
def tl(pos):
    px, py =  pos.x, pos.y
    sz = size / 2
    x, y = (px*sz)-0, (py*sz)+0
    return x, y

class GraphicsItem(QtGui.QGraphicsItem):
    def __init__(self):
        QtGui.QGraphicsItem.__init__(self)

    def set_transform(self):
        cx, cy = self.cx, self.cy
        x, y = self.pos
        x -= cx
        y -= cy
        ang = self.ang

        trans = QtGui.QTransform()
        trans.translate(x, y)
        trans.translate(cx, cy).rotate(ang).translate(-cx, -cy)
        self.setTransform(trans)

    def setpos(self, pos):
        self.pos = pos
        self.set_transform()

    def set_rotation(self, ang):
        self.ang = -(180/pi)*ang
        self.set_transform()

    def rotate(self, deg):
        self.ang += deg
        self.set_transform()

    def paint(self, painter, option, widget):
        pass

    def kill(self):
        scene = self.item.scene()
        scene.removeItem(self.item)

class Robot(GraphicsItem):
    nrobots = 0
    def __init__(self, pos, ang, rend):
        Robot.nrobots += 1

        self.pos = tl(pos)
        self.ang = ang
        self.scale = 1
        self.cx, self.cy = 15, 15

        GraphicsItem.__init__(self)

        imageid = 'r{0:02d}'.format(Robot.nrobots)
        self.item = QtSvg.QGraphicsSvgItem(self)
        self.item.setSharedRenderer(rend)
        self.item.setElementId(imageid)

        self.turr = Turret(self, rend)

        self.set_transform()

    def setpos(self, pos):
        self.pos = tl(pos)
        self.set_transform()

    def boundingRect(self):
        return self.item.boundingRect()

    def set_turr_rot(self, ang):
        self.turr.set_rotation(ang)


class Turret(GraphicsItem):
    def __init__(self, robot, rend):
        self.pos = 15, 15
        self.ang = 0
        self.scale = 1
        self.cx, self.cy = 15, 15

        GraphicsItem.__init__(self)

        self.item = QtSvg.QGraphicsSvgItem(robot.item)
        self.item.setSharedRenderer(rend)
        self.item.setElementId('turret')
        self.set_transform()

    def set_transform(self):
        cx, cy = self.cx, self.cy
        x, y = self.pos
        x -= cx
        y -= cy
        ang = self.ang

        trans = QtGui.QTransform()
        trans.translate(x, y)
        trans.translate(cx, cy).rotate(ang).translate(-cx, -cy)
        self.item.setTransform(trans)


class Bullet(GraphicsItem):
    def __init__(self, pos, scene):
        self.pos = tl(pos)
        self.ang = 0
        self.scale = 1
        self.cx, self.cy = 2, 2

        GraphicsItem.__init__(self)

        self.item = scene.addEllipse(0, 0, 4, 4)
        self.item.setParentItem(self)
        color = QtGui.QColor(200, 200, 200)
        brush = QtGui.QBrush(color)
        self.item.setBrush(brush)
        self.set_transform()

    def setpos(self, pos):
        self.pos = tl(pos)
        self.set_transform()

    def boundingRect(self):
        return self.item.boundingRect()


class Wall(object):
    def __init__(self, pos, size):
        pass

class RobotInfo(QtGui.QHBoxLayout):
    def __init__(self, n, name, rend):
        QtGui.QHBoxLayout.__init__(self)

        icon = QtGui.QPixmap(50, 50)
        icon.fill(QtCore.Qt.transparent)
        self.icon = icon
        painter = QtGui.QPainter(icon)
        self.painter = painter # need to hold this or Qt throws an error
        imageid = 'r{0:02d}'.format(n)
        rend.render(painter, imageid)
        iconl = QtGui.QLabel()
        iconl.setPixmap(icon)

        vl = QtGui.QVBoxLayout()
        nm = QtGui.QLabel(name)
        nm.setFont(QtGui.QFont('Serif', 14))
        vl.addWidget(nm)

        self.health = Health()
        vl.addWidget(self.health)

        self.addWidget(iconl)
        self.addLayout(vl)

        #r = QtCore.QRect(0, 0, 300, 50)
        #self.setGeometry(r)



class Health(QtGui.QProgressBar):
    def __init__(self):
        QtGui.QProgressBar.__init__(self)
        self.setMaximum(conf.maxhealth)
        self.setMinimum(0)
        self._val = conf.maxhealth
        self.setValue(self._val)

    def step(self, n=None):
        if n is not None:
            self._val -= n
        else:
            self._val -= 1

        if self._val < 0:
            self._val = 0

        self.setValue(self._val)
        if self._val <= 0.30 * conf.maxhealth:
            pal = self.palette()
            pal.setColor(QtGui.QPalette.Highlight, QtGui.QColor('red'))
            self.setPalette(pal)

class Explosion(GraphicsItem):
    def __init__(self, pos, scene):
        self.pos = tl(pos)
        self.ang = 0
        self.scale = 1
        self.cx, self.cy = 45, 45

        GraphicsItem.__init__(self)

        self.item0 = scene.addEllipse(0, 0, 90, 90)
        self.item0.setParentItem(self)
        color = QtGui.QColor(250, 200, 0)
        brush = QtGui.QBrush(color)
        self.item0.setBrush(brush)

        self.item1 = scene.addEllipse(15, 15, 60, 60)
        self.item1.setParentItem(self)
        color = QtGui.QColor(200, 100, 100)
        brush = QtGui.QBrush(color)
        self.item1.setBrush(brush)
        self.item1.setParentItem(self.item0)

        self.item2 = scene.addEllipse(30, 30, 30, 30)
        self.item2.setParentItem(self)
        color = QtGui.QColor(200, 50, 50)
        brush = QtGui.QBrush(color)
        self.item2.setBrush(brush)
        self.item2.setParentItem(self.item1)

        self.set_transform()

    def boundingRect(self):
        return self.item0.boundingRect()

    def setpos(self, pos):
        self.pos = tl(pos)
        self.set_transform()

    def set_rotation(self, ang):
        pass

    def kill(self):
        scene = self.item0.scene()
        scene.removeItem(self.item0)


class Arena(object):
    def setrend(self):
        self.rend = getrend(self.app)

    def addrobot(self, pos, ang):
        v = Robot(pos, ang, self.rend)
        self.scene.addItem(v)
        v.setParentItem(self.scene.arenarect)
        return v

    def addrobotinfo(self, n, name):
        ri = RobotInfo(n, name, self.rend)
        self.rinfo.addLayout(ri)
        #print 'rinfo22', self.rinfo
        #print 'ri', self.rinfo.geometry()
        return ri

    def addbullet(self, pos):
        v = Bullet(pos, self.scene)
        self.scene.addItem(v)
        v.setParentItem(self.scene.arenarect)
        return v

    def addexplosion(self, pos):
        e = Explosion(pos, self.scene)
        self.scene.addItem(e)
        e.setParentItem(self.scene.arenarect)
        return e

    def step(self, x=None):
        pass


class Splash(QtGui.QSplashScreen):
    def __init__(self, app):
        rend = getrend(app)
        img = QtGui.QPixmap(500, 250)
        img.fill(QtCore.Qt.transparent)
        self.img = img
        painter = QtGui.QPainter(img)
        self.painter = painter # need to hold this or Qt throws an error
        rend.render(painter, 'splash')
        QtGui.QSplashScreen.__init__(self, img)
        self.setMask(img.mask())



def run():
    app = QtGui.QApplication(sys.argv)

    splash = Splash(app)
    splash.show()

    win = MainWindow(app)
    win.show()
    splash.finish(win)
    app.exec_()


if __name__ == "__main__":
    run()
