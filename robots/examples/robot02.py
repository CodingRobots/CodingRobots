from robot import Robot

class TheRobot(Robot):
    def respond(self):
        self.ping()
        self.ping_react()

    def ping_react(self):
        kind, angle, dist = self.sensors['PING']

        if kind == 'w':
            # Pinged a wall

            if dist < 2:
                self.force(-30)
                self.torque(50)
            else:
                self.force(60)
                self.torque(0)

        elif kind in 'rb':
            # Pinged a robot or a bullet

            self.fire()

            if dist < 5:
                self.force(-10)
            else:
                self.force(10)
                self.torque(30)
