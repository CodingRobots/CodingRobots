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
from threading import Thread
from time import sleep

from util import defaultNonedict

import conf


_overtime_count = 0

def loop(r, i):
    data = i.split('|')
    sensors = defaultNonedict()
    for d in data:
        k, v = d.split(':')

        if ';' in v:
            # Some sensors send multiple values, separated by semicolon
            v = v.split(';')
            vconv = []
            for vv in v:
                try:
                    vvconv = int(vv)
                except:
                    vvconv = vv

                vconv.append(vvconv)

        else:
            try:
                vconv = int(v)
            except:
                vconv = v

        sensors[k] = vconv

    timeout = conf.tick_timeout

    user_thread = Thread(target=get_response, args=(r, sensors))
    response = None
    user_thread.start()

    user_thread.join(timeout)
    if user_thread.isAlive():
        global _overtime_count
        _overtime_count += 1
        response = 'TIMEOUT'
        if _overtime_count > 10:
            os.kill(os.getpid(), 9)
    else:
        _overtime_count = 0

    return response or r.response

def get_response(r, sensors):
    try:
        r.sensors = sensors
        r.respond()
    except Exception, e:
        r.err()
        import traceback
        tb = traceback.format_exc()
        r.log(tb)

def communicate(r):
    while True:
        sleep(0.015)
        line = sys.stdin.readline().strip()
        if line == 'FINISH':
            break

        o = loop(r, line)
        if o is not None:
            oline = '%s\n' % (str(o))
            try:
                sys.stdout.write(oline)
                sys.stdout.flush()
            except IOError:
                break
        else:
            oline = 'END\n'
            try:
                sys.stdout.write(oline)
                sys.stdout.flush()
            except IOError:
                pass
            break


def build_robot(modname, robotname, testmode, rbox):

    if testmode:
        logfilename = '%s.log' % robotname
        logfilepath = os.path.join(conf.logdir, logfilename)
        logfile = open(logfilepath, 'a')
    else:
        logfile = None

    try:
        mod = __import__(modname)
        r = mod.TheRobot(robotname)

        r.logfile = logfile

        r.initialize()

    except:
        rbox.append(None)

        import traceback
        tb = traceback.format_exc()
        if logfile is not None:
            logfile.write(tb)
            logfile.write('\n')
            logfile.flush()
        else:
            import sys
            sys.stderr.write(tb)
            sys.stderr.write('\n')
            sys.stderr.flush()

    else:
        rbox.append(r)


if __name__ == '__main__':
    import sys
    for d in conf.robot_dirs:
        sys.path.append(d)

    if len(sys.argv) != 4:
        raise SystemExit
    else:
        modname = sys.argv[1]
        robotname = sys.argv[2]
        testmode = bool(int(sys.argv[3]))

        timeout = conf.init_timeout

        rbox = [] # Store the robot here to pass it back from the thread
        user_thread = Thread(target=build_robot, args=(modname, robotname, testmode, rbox))
        user_thread.start()

        user_thread.join(timeout)
        if user_thread.isAlive():
            rbox = [None]

        robot = rbox[0]

        if robot is None:
            # robot failed to load properly
            oline = 'ERROR\n'
            sys.stdout.write(oline)
            sys.stdout.flush()

        else:
            oline = 'START\n'
            sys.stdout.write(oline)
            sys.stdout.flush()
            try:
                communicate(robot)
            except KeyboardInterrupt:
                pass
