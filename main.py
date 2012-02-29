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

import viewselect

if __name__ == '__main__':
    import sys
    import os

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
    parser.add_option("-D", "--upgrade-db", dest="upgrade_db",
                    action="store_true", default=False,
                    help="upgrade database (WARNING! Deletes database!)")
    parser.add_option("-R", "--robots", dest="robots",
            action="store", type='str', default='',
                    help="Specify which robots to battle")
    parser.add_option("-I", "--gameid", dest="gameid",
                    action="store",type='str',default='nope',
                    help="Specify the game id for storing data in nosql")

    (options, args) = parser.parse_args()

    testmode = options.testmode
    tournament = options.tournament
    nbattles = options.nbattles
    nographics = options.nographics
    pyqtgraphics = options.pyqtgraphics
    upgrade_db = options.upgrade_db
    gamerobots = options.robots.split(" ")
    gameID = options.gameid

    if nographics:
        viewselect.select_view_module('none')
    elif not pyqtgraphics:
        viewselect.select_view_module('pygame')
    else:
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



def runmain():
    if upgrade_db:
        stats.dbremove()
        stats.initialize()

    dbcheck()

    global testmode
    if testmode:
        if not os.path.exists(conf.logdir):
            print 'Log directory does not exist:', conf.logdir
            print 'test mode disabled'
            testmode = False

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
        qt4view.run()

    else:
        game = Game(testmode, gameID=gameID,robots=gamerobots)
        game.run()

    stats.dbclose()

    # Clean up log directory if not in test mode
    if not testmode and os.path.exists(conf.logdir):
        for f in os.listdir(conf.logdir):
            fpath = os.path.join(conf.logdir, f)
            os.remove(fpath)


if __name__ == '__main__':
    try:
        runmain()
    except KeyboardInterrupt:
        pass

