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


import time

try:
    import conf
except ImportError:
    import util
    util.makeconf()

    import stats
    stats.dbcheck()

    raise SystemExit

import util
import viewselect


def setup_logging(level='info'):
    import logging
    import logging.handlers
    logger = logging.getLogger('PybotwarLogger')
    logger.setLevel(logging.INFO)
    handler = logging.handlers.RotatingFileHandler(
              'appdebug.log', maxBytes=1000000, backupCount=3)
    logger.addHandler(handler)


if __name__ == '__main__':
    import sys
    import os

    os.chdir(os.path.split(os.path.abspath(__file__))[0])

    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-T", "--testmode", dest="testmode",
                    action="store_true", default=False,
                    help="run in test mode")
    parser.add_option("-t", "--tournament", dest="tournament",
                    action="store_true", default=False,
                    help="run a tournament")
    parser.add_option("-n", "--battles", dest="nbattles",
                    action="store", type='int', default=5,
                    help="number of battles in tournament")
    parser.add_option("-g", "--no-graphics", dest="nographics",
                    action="store_true", default=False,
                    help="non graphics mode")
    parser.add_option("-Q", "--pyqt-graphics", dest="pyqtgraphics",
                    action="store_true", default=False,
                    help="enable PyQt interface")
    parser.add_option("-P", "--pygsear-graphics", dest="pygseargraphics",
                    action="store_true", default=False,
                    help="enable Pygsear interface")
    parser.add_option("-D", "--upgrade-db", dest="upgrade_db",
                    action="store_true", default=False,
                    help="upgrade database (WARNING! Deletes database!)")
    parser.add_option("-S", "--reset-qt-settings", dest="qtreset",
                    action="store_true", default=False,
                    help="reset Qt settings")
    parser.add_option("-B", "--app-debug", dest="appdebug",
                    action="store_true", default=False,
                    help="enable app debug log")

    (options, args) = parser.parse_args()

    testmode = options.testmode
    tournament = options.tournament
    nbattles = options.nbattles
    nographics = options.nographics
    pyqtgraphics = options.pyqtgraphics
    pygseargraphics = options.pygseargraphics
    upgrade_db = options.upgrade_db
    qtreset = options.qtreset
    appdebug = options.appdebug

    gmodes = nographics + pyqtgraphics + pygseargraphics

    if appdebug:
        setup_logging()

    if gmodes > 1:
        print 'must select ONE of -g, -Q, or -P'
        import sys
        sys.exit(0)

    elif nographics:
        viewselect.select_view_module('none')
    elif pyqtgraphics:
        viewselect.select_view_module('pyqt')
    elif pygseargraphics:
        viewselect.select_view_module('pygame')
    else:
        # default view type is PyQt
        pyqtgraphics = True
        viewselect.select_view_module('pyqt')

view = viewselect.get_view_module()

from game import Game

import world
from world import box2d

import stats


def dbcheck():
    if not stats.dbcheck():
        print 'Run pytbotwar with -D switch to upgrade database.'
        print 'WARNING: This will delete your current database!'
        import sys
        sys.exit(0)


def reset_qt_settings():
    from PyQt4 import QtCore
    QtCore.QCoreApplication.setOrganizationName('pybotwar.googlecode.com')
    QtCore.QCoreApplication.setOrganizationDomain('pybotwar.googlecode.com')
    QtCore.QCoreApplication.setApplicationName('pybotwar')
    settings = QtCore.QSettings()
    settings.clear()
    print 'Qt settings cleared.'


def runmain():
    if qtreset:
        reset_qt_settings()

    if upgrade_db:
        print 'Upgrading Database'
        stats.dbremove()
        stats.initialize()
        return

    dbcheck()

    stats.dbopen()

    if tournament:
        import datetime
        dt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print 'Beginning tournament with %s battles.' % nbattles
        for battle in range(nbattles):
            print 'Battle', battle+1
            game = Game(testmode, dt)
            game.run()
            world.Robot.nrobots = 0
            view.Robot.nrobots = 0

        results = stats.tournament_results(dt)
        print;print;print;
        print 'Tournament Results'
        print nbattles, 'battles between', len(results), 'robots'
        print
        for line in results:
            print line[1], ':', line[4], 'wins', ':', line[6], 'defeated', ':', line[7], 'dmg caused'

    elif pyqtgraphics:
        import qt4view
        qt4view.run(testmode)

    else:
        game = Game(testmode)
        game.run()

    stats.dbclose()

    if not tournament:
        stats.dbopen()
        stats.top10()


    # Clean up log directory if not in test mode
    rdirs = util.get_robot_dirs()
    robotsdir = rdirs[0]
    logdir = os.path.join(robotsdir, conf.logdir)

    if not testmode and os.path.exists(logdir):
        for f in os.listdir(logdir):
            fpath = os.path.join(logdir, f)
            try:
                os.remove(fpath)
            except OSError:
                pass


if __name__ == '__main__':
    try:
        runmain()
    except KeyboardInterrupt:
        pass

