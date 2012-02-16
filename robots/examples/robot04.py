from robot import Robot

class TheRobot(Robot):
    def initialize(self):
        # Try to get in to a corner
        self.forseconds(5, self.force, 50)
        self.forseconds(0.9, self.force, -10)
        self.forseconds(0.7, self.torque, 100)
        self.forseconds(6, self.force, 50)

        # Then look around and shoot stuff
        self.forever(self.scanfire)


        self._turretdirection = 1
        self.turret(180)
        self._pingfoundrobot = None

    def scanfire(self):
        self.ping()

        sensors = self.sensors
        kind, angle, dist = sensors['PING']
        tur = sensors['TUR']

        if self._pingfoundrobot is not None:
            # has pinged a robot previously
            if angle == self._pingfoundrobot:
                # This is where we saw the robot previously
                if kind in 'rb':
                    # Something is still there, so shoot it
                    self.fire()
                else:
                    # No robot there now
                    self._pingfoundrobot = None
            elif kind == 'r':
                # This is not where we saw something before,
                #   but there is a robot at this location also
                self.fire()
                self._pingfoundrobot = angle
                self.turret(angle)
            else:
                # No robot where we just pinged. So go back to
                #   where we saw a robot before.
                self.turret(self._pingfoundrobot)

        elif kind == 'r':
            # pinged a robot
            # shoot it
            self.fire()
            # keep the turret here, and see if we can get it again
            self._pingfoundrobot = angle
            self.turret(angle)

        else:
            # No robot pinged, and have not seen a robot yet
            #   so move the turret and keep looking
            if self._turretdirection == 1:
                if tur < 180:
                    self.turret(180)
                else:
                    self._turretdirection = 0
            elif self._turretdirection == 0:
                if tur > 90:
                    self.turret(90)
                else:
                    self._turretdirection = 1
