from robot import Robot

class TheRobot(Robot):
    def initialize(self):
        self.health = 100

        self._turnto = 5

        self._moveto_choices = [70, 70, -70, -70]

    def respond(self):
        tick = self.sensors['TICK']
        if tick == 100:
            self.start_logging()
        elif tick == 200:
            self.stop_logging()

        self.scan_and_fire()

        # Move away if damaged
        health = self.sensors['HEALTH']
        if health != self.health:
            self.health = health
            self._turnto += 1

        self.turnto()
        self.moveto()

    def turnto(self):
        # Turn to angle set by self._turnto

        turnto = 90 * self._turnto

        gyro = self.sensors['GYRO']

        gain = 2.5
        error = gyro - turnto
        torque = -gain * error

        self.torque(torque)

    def moveto(self):
        # Move to the position set in self._moveto

        moveto = self._moveto_choices[self._turnto%4]

        pos = self.sensors['POS']

        gain = 6
        coord = pos[self._turnto%2]
        sign = [-1, -1, 1, 1][self._turnto%4]
        error = coord - moveto
        force = max(min(10, sign * gain * error), -10)

        self.log(pos, sign, coord, moveto, force, self._turnto, self.sensors['GYRO'])

        self.force(force)

    def scan_and_fire(self):
        # Move the turret around, look for stuff and shoot it

        tur = self.sensors['TUR']
        self.turret(tur-20)
        self.ping()

        kind, angle, dist = self.sensors['PING']
        if kind in 'r':
            if dist > 4:
                # Try not to blast yourself
                self.fire(dist)
            else:
                self.fire()
