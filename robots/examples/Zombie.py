from robot import Robot

class TheRobot(Robot):
    def initialize(self):
        self.health = 100
        self._movefor = 0
        self._moveforce = 0
        self._turnto = 0

    def respond(self):
        self.turnto()
        self.scan_and_fire()

        # Move away if damaged
        health = self.sensors['HEALTH']
        if health != self.health:
            self.health = health
            self._movefor = 60 #ticks
            self._moveforce = 100
            self._turnto += 90

        if self._movefor:
            self._movefor -= 1
            self.force(self._moveforce)
        else:
            self.force(0)

    def turnto(self):
        # Turn to angle set in self._turnto

        gyro = self.sensors['GYRO']

        gain = 0.5
        error = gyro - self._turnto
        torque = -gain * error

        self.torque(torque)

    def scan_and_fire(self):
        # Move the turret around, look for stuff and shoot it

        tur = self.sensors['TUR']
        self.turret(tur+20)
        self.ping()

        kind, angle, dist = self.sensors['PING']
        if kind in 'rb':
            if dist > 4:
                # Try not to blast yourself
                self.fire(dist)
            else:
                self.fire()
