import random
from math import pi

from robot import Robot

class TheRobot(Robot):
    def initialize(self):
        self.ctrlr = self.controller()

    def respond(self):
        try:
            self.ctrlr.next()
        except StopIteration:
            self.finished()

    def controller(self):
        'Set up a generator to keep state between calls.'

        while True:
            for t in self.setturret(): yield
            for t in self.square(): yield
            for t in self.patrol(): yield
            for t in self.unstick(): yield

    def setturret(self):
        # Turn the turret to a random position
        angle = random.randrange(-180, 180)
        self.turret(angle)
        yield

    def square(self):
        # Go in a square
        for side in range(4):
            for t in self.fwdfor(2): yield
            self.fire(); yield
            for t in self.rightfor(1.0): yield
            self.fire(); yield

    def patrol(self):
        # Go back and forth in a line
        for side in range(2):
            for t in self.fwdfor(3): yield
            self.fire(); yield
            for t in self.rightfor(1.9): yield
            self.fire(); yield
            self.ping(); yield

    def unstick(self):
        # Try to get unstuck if up against a wall
        self.log('test unstick log')
        for t in self.fwdfor(-1): yield
        for t in self.rightfor(-1.5): yield

    def fwdfor(self, s):
        'Move forward for s seconds, or keep going if s is None.'

        force = 50
        if s < 0:
            s = -s
            force = -force

        t = 60 * s

        while t > 0:
            self.force(force)
            yield t
            t -= 1
        else:
            self.force(0)

    def rightfor(self, s):
        'Turn right for s seconds, or keep turning if s is None.'

        torque = 100
        if s < 0:
            s = -s
            torque = -torque

        t = 60 * s

        while t > 0:
            self.torque(torque)
            yield t
            t -= 1
        else:
            self.torque(0)

