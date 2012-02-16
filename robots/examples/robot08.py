# This example was used in verifying the problem outlined
# in issue #5 in the bug tracker.

from robot import Robot

class TheRobot(Robot):
    def respond(self):
        self.turret(0)
        self.pingcheck()

    def pingcheck(self):
        g = self.sensors['GYRO']
        if -2 <= g <= 2:
            self.ping()
            p = self.sensors['PING']
            self.force(5)
            x, y = self.sensors['POS']
            self.log(p, x)
        else:
            self.torque(-0.45 * g)
            self.log(g)
