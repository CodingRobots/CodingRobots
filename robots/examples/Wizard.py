import random
from robot import Robot


class TheRobot(Robot):
    def initialize(self):
        self._state = 'FORWARD'
        self._fwdfor_ticks = None
        self._rightfor_ticks = None
        self._unstick_freq = 12
        self._unstickfor_ticks = None

    def respond(self):
        self.controller()

    def controller(self):
        self.shoot()

        if self._state == 'FORWARD':
            if self._fwdfor_ticks is not None:
                self.fwdfor()
            else:
                self._state = 'RIGHT'
                self.rightfor(0.8)

        elif self._state == 'RIGHT':
            if self._rightfor_ticks is not None:
                self.rightfor()
            else:
                self._unstick_freq -= 1
                if self._unstick_freq < 0:
                    self._state = 'UNSTICK'
                    self.unstickfor(1.6)
                else:
                    self._state = 'FORWARD'
                    self.fwdfor(1)

        elif self._state == 'UNSTICK':
            if self._unstickfor_ticks is not None:
                self._unstick_freq = 12
                self.unstickfor()
            else:
                self._state = 'FORWARD'
                self.fwdfor(1)

    def shoot(self):
        # Fire the cannon occasionally
        if not random.randrange(3):
            self.fire()

    def fwdfor(self, s=None):
        'Move forward for s seconds, or if s is None, keep moving forward.'

        if s is None:
            t = self._fwdfor_ticks
            t -= 1
        else:
            t = 60 * s

        if t > 0:
            self.force(100)
        else:
            t = None
            self.force(0)

        self._fwdfor_ticks = t
        return t

    def rightfor(self, s=None):
        'Turn right for s seconds, or if s is None, keep turning right.'

        if s is None:
            t = self._rightfor_ticks
            t -= 1
        else:
            t = 60 * s

        if t > 0:
            self.torque(100)
        else:
            t = None
            self.torque(0)

        self._rightfor_ticks = t
        return t

    def unstickfor(self, s=None):
        'Back up and turn left for s seconds, or if s is None, keep on...'

        if s is None:
            t = self._unstickfor_ticks
            t -= 1
        else:
            self.log('unstick!')
            t = 60 * s

        if t > 0:
            self.force(-60)
            self.torque(-100)
        else:
            t = None
            self.force(0)
            self.torque(0)

        self._unstickfor_ticks = t
        return t
