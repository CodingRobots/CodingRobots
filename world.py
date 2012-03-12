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


import random

import Box2D as box2d
pi = 3.1415927410125732

import conf

import viewselect
view = viewselect.get_view_module()


def pos_tuple_scale(pos):
    min_x = 30
    min_y = 25
    return ((pos.x+min_x)*50./min_x, (pos.y+min_y)*50./min_y)


def size_tuple_scale(pos_x, pos_y):
    min_x = 30
    min_y = 25
    return (pos_x*100./min_x, pos_y*100./min_y)


class Robot(object):
    nrobots = 0
    def __init__(self, wld, kind, name, pos, ang):
        w = wld.w

        Robot.nrobots += 1
        self.n = Robot.nrobots

        self.alive = True
        self.health = conf.maxhealth
        self.kind = kind
        self.name = name

        self._pingtype = 'w'
        self._pingangle = 0
        self._pingdist = 0

        self._pinged = -5 # Tick most recently pinged by another robot's radar

        self._cannonheat = 0
        self._cannonreload = 0

        self._kills = 0 # number of robots killed while this one is still alive
        self._damage_caused = 0

        bodyDef = box2d.b2BodyDef()
        bodyDef.position = pos
        bodyDef.angle = ang

        bodyDef.linearDamping = conf.robot_linearDamping
        bodyDef.angularDamping = conf.robot_angularDamping
        bodyDef.userData = {}

        body = w.CreateBody(bodyDef)

        shapeDef = box2d.b2PolygonDef()
        shapeDef.SetAsBox(1, 1)
        shapeDef.density = conf.robot_density
        shapeDef.friction = conf.robot_friction
        shapeDef.restitution = conf.robot_restitution
        shapeDef.filter.groupIndex = -self.n
        body.CreateShape(shapeDef)
        body.SetMassFromShapes()

        body.userData['actor'] = self
        body.userData['kind'] = 'robot'

        self.body = body

        turretDef = box2d.b2BodyDef()
        turretDef.position = pos
        turretDef.angle = ang

        turretDef.linearDamping = 0
        turretDef.angularDamping = 0
        turret = w.CreateBody(bodyDef)

        shapeDef = box2d.b2PolygonDef()
        shapeDef.SetAsBox(.1, .1)
        shapeDef.density = 1
        shapeDef.friction = 0
        shapeDef.restitution = 0
        shapeDef.filter.groupIndex = -self.n
        turret.CreateShape(shapeDef)
        turret.SetMassFromShapes()
        self.turret = turret

        jointDef = box2d.b2RevoluteJointDef()
        jointDef.Initialize(body, turret, pos)
        jointDef.maxMotorTorque = conf.turret_maxMotorTorque
        jointDef.motorSpeed = 0.0
        jointDef.enableMotor = True
        self.turretjoint = w.CreateJoint(jointDef).getAsType()
        self._turretangletarget = 0

        v = wld.v.addrobot(pos, ang)
        self.v = v

        i = wld.v.addrobotinfo(self.n, name)
        self.i = i

    def to_dict(self):
        roboDict = {}
        roboDict['position'] = pos_tuple_scale(self.body.position)
        roboDict['rotation'] = self.gyro()
        roboDict['health'] = self.health
        roboDict['name'] = self.name
        roboDict['turret_angle'] = self.get_turretangle()
        return roboDict

    def gyro(self):
        'return robot angle wrt world in degrees.'
        radians = self.body.angle
        degrees = int(round((180 / pi) * radians))
        return degrees

    def set_turretangle(self, angle):
        'Angle comes in degrees. Convert to radians and set.'
        radians = (pi / 180.) * angle
        self._turretangletarget = radians

    def get_turretangle(self):
        'return turret angle in degrees.'
        degrees = int(round((180 / pi) * self.turretjoint.GetJointAngle()))
        return degrees

    def turretcontrol(self):
        joint = self.turretjoint
        angleError = joint.GetJointAngle() - self._turretangletarget
        gain = 0.5
        joint.SetMotorSpeed(-gain * angleError)


class Bullet(object):
    def __init__(self, wld, robot):
        self.wld = wld
        w = wld.w
        self.robot = robot # Fired by this robot

        self._fuse = None
        self._exploding = False

        r = robot.turret
        pos = r.position
        vel = r.linearVelocity
        ang = r.angle

        blocalvel = box2d.b2Vec2(conf.bulletspeed, 0)
        bwvel = r.GetWorldVector(blocalvel)
        bvel = bwvel + vel
        #print bvel, bvel.Length()

        bodyDef = box2d.b2BodyDef()
        blocalpos = box2d.b2Vec2(.1, 0)
        bwpos = r.GetWorldVector(blocalpos)
        bpos = bwpos + pos
        bodyDef.position = bpos
        bodyDef.angle = ang
        bodyDef.isBullet = True
        bodyDef.linearDamping = 0
        bodyDef.userData = {}

        body = w.CreateBody(bodyDef)
        #print body
        #print 'IB', body.isBullet
        body.linearVelocity = bvel

        shapeDef = box2d.b2PolygonDef()
        shapeDef.SetAsBox(.1, .1)
        shapeDef.density = conf.bullet_density
        shapeDef.restitution = 0
        shapeDef.friction = 0
        shapeDef.filter.groupIndex = -robot.n
        b = body.CreateShape(shapeDef)
        b.userData = {}
        body.SetMassFromShapes()

        body.userData['actor'] = self
        body.userData['kind'] = 'bullet'
        body.userData['shooter'] = robot

        self.body = body

        v = wld.v.addbullet(pos)
        self.v = v
    def to_dict(self):
        bulletDict = {}
        bulletDict['position'] = pos_tuple_scale(self.body.position)
        bulletDict['angle'] = self.body.angle
        bulletDict['exploding'] = 0 if not self._exploding else self._exploding
        return bulletDict

    def explode(self):
        self._exploding = 1

        #robot = self.body.userData['shooter'].name
        #print robot,'bullet explode at', self.body.position

        for ring, radius in enumerate(conf.explosion_radii):
            cdef = box2d.b2CircleDef()
            cdef.radius = radius

            s = self.body.CreateShape(cdef)
            s.userData = {}
            s.userData['ring'] = ring
            s.userData['bullet'] = self
            s.userData['hits'] = {0:[], 1:[], 2:[]}

        e = self.wld.v.addexplosion(self.body.position)
        self.e = e

class Wall(object):
    def __init__(self, w, pos, size):
        walldef = box2d.b2BodyDef()
        walldef.position = pos
        walldef.userData = {}
        wallbod = w.CreateBody(walldef)
        wallbod.userData['actor'] = None
        wallbod.userData['kind'] = 'wall'
        wallbod.iswall = True
        wallshp = box2d.b2PolygonDef()
        width, height = size
        wallshp.SetAsBox(width, height)
        wallbod.CreateShape(wallshp)
        self.body = wallbod
        self.width = size[0]
        self.height = size[1]
        v = view.Wall(pos, size)
        self.v = v
    def to_dict(self):
        wallDict = {}
        wallDict['position'] = pos_tuple_scale(self.body.position)
        (width, height) = size_tuple_scale(self.width, self.height)
        wallDict['width'] = width
        wallDict['height'] = height
        return wallDict

class World(object):
    def __init__(self):
        self.count = 1000
        self.force = 10

        self.robots = {}
        self.bullets = []
        self.sprites = {}
        self.walls = []
        self.to_destroy = []

        halfx = 30
        self.ahalfx = 20
        halfy = 25
        self.ahalfy = 20

        gravity = (0, 0)
        doSleep = True

        self.timeStep = 1.0 / 60.0
        self.velIterations = 10
        self.posIterations = 8


        aabb = box2d.b2AABB()
        aabb.lowerBound = (-halfx, -halfy)
        aabb.upperBound = (halfx, halfy)

        self.w = box2d.b2World(aabb, gravity, doSleep)
        self.w.GetGroundBody().SetUserData({'actor': None})

        self.makearena()


    def makearena(self):
        self.v = view.Arena()

        ahx = self.ahalfx
        ahy = self.ahalfy

        self.walls.append(Wall(self.w, (-ahx, 0), (1, ahy+1)))
        self.walls.append(Wall(self.w, (ahx, 0), (1, ahy+1)))
        self.walls.append(Wall(self.w, (0, ahy), (ahx+1, 1)))
        self.walls.append(Wall(self.w, (0, -ahy), (ahx+1, 1)))

        for block in range(5):
            #self.makeblock()
            pass

    def makeblock(self):
        x = random.randrange(-self.ahalfx, self.ahalfx+1)
        y = random.randrange(-self.ahalfy, self.ahalfy+1)
        w = random.randrange(1, 20)/10.0
        h = random.randrange(1, 20)/10.0
        wl = Wall(self.w, (x, y), (w, h))

    def posoccupied(self, pos):
        px, py = pos.x, pos.y
        for name, robot in self.robots.items():
            rbpos = robot.body.position
            rx, ry = rbpos.x, rbpos.y
            if (rx-2 < px < rx+2) and (ry-2 < py < ry+2):
                return True

        return False

    def makerobot(self, kind, name, pos=None, ang=None):
        rhx = self.ahalfx-2
        rhy = self.ahalfy-2

        while pos is None or self.posoccupied(pos):
            rx = random.randrange(-rhx, rhx)
            ry = random.randrange(-rhy, rhy)
            pos = box2d.b2Vec2(rx, ry)

        if ang is None:
            ang = random.randrange(628) / float(100)

        robot = Robot(self, kind, name, pos, ang)
        self.robots[name] = robot

        return robot

    def makebullet(self, rname, fuse=None):
        robot = self.robots[rname]
        if robot._cannonheat > conf.cannon_maxheat:
            # tried to fire when the cannon was overheated
            robot._cannonreload += conf.overheat_fire_reload_penalty
            return None
        elif robot._cannonreload > 0:
            # tried to fire when the cannon was not loaded
            robot._cannonreload += conf.unloaded_fire_reload_penalty
            return None

        bullet = Bullet(self, robot)
        bullet._fuse = fuse
        self.bullets.append(bullet)

        robot._cannonheat += conf.cannon_heating_per_shot
        robot._cannonreload = conf.cannon_reload_ticks

        return bullet

    def makeping(self, rname, rnd):
        robot = self.robots[rname]
        body = robot.turret

        segmentLength = 65.0

        blocalpos = box2d.b2Vec2(1.12, 0)

        segment = box2d.b2Segment()
        laserStart = (1.12, 0)
        laserDir = (segmentLength, 0.0)
        segment.p1 = body.GetWorldPoint(laserStart)
        segment.p2 = body.GetWorldVector(laserDir)
        segment.p2+=segment.p1

        lambda_, normal, shape = self.w.RaycastOne(segment, False, None)
        hitp = (1 - lambda_) * segment.p1 + lambda_ * segment.p2
        angle = robot.get_turretangle()
        dist = box2d.b2Distance(segment.p1, hitp)

        if shape is not None:
            hitbody = shape.GetBody()
            kind = hitbody.userData['kind']
            if kind == 'robot':
                actor = hitbody.userData['actor']
                if actor._pinged != rnd - 1:
                    actor._pinged = rnd
            return kind, angle, dist
        else:
            # Not sure why shape returns None here. Seems to be when the
            #   robot is pressed right up against a wall, though.
            return 'w', angle, 0

    def step(self):
        #self.moveit()
        #print 'STEP', self.w.Step
        self.w.Step(self.timeStep, self.velIterations, self.posIterations)
        self.do_destroy()
        self.showit()


    def showit(self):
        for name, robot in self.robots.items():
            r = robot.body
            robot.turretcontrol()
            #vel = r.linearVelocity.Length()
            #pos = r.position.Length()
            pos2 = r.position
            ang = r.angle

            turret = robot.turretjoint
            tang = turret.GetJointAngle()

            #print '{name}: {pos:6.2f} {ang:5.1f} {vel:5.1f}'.format(
            #           name=name, vel=vel, pos=pos, ang=ang)

            robot.v.setpos(pos2)
            robot.v.set_rotation(-ang)

            #robot.t.setpos(pos2)
            robot.v.set_turr_rot(-tang)

            if robot._cannonheat > 0:
                robot._cannonheat -= conf.cannon_cooling_per_tick
            if robot._cannonreload > 0:
                robot._cannonreload -= 1

        for bullet in self.bullets:
            b = bullet.body
            pos2 = b.position
            bullet.v.setpos(pos2)
            #print bullet.linearVelocity

            if bullet._fuse is not None:
                bullet._fuse -= 1
                if bullet._fuse == 0:
                    print 'shell explodes'
                    bullet.explode()

            if bullet._exploding:
                if bullet._exploding > 2:
                    if bullet not in self.to_destroy:
                        self.to_destroy.append(bullet)
                else:
                    bullet._exploding += 1

        #print
        self.v.step()

    def do_destroy(self):
        while self.to_destroy:
            model = self.to_destroy.pop()
            body = model.body
            if hasattr(body, 'iswall') and body.iswall:
                continue
            #print 'destroy', id(body)
            if model in self.bullets:
                self.bullets.remove(model)
                if model._exploding:
                    model.e.kill()
            #print 's0', self.v.sprites
            model.v.kill()

            if model.body.userData['kind'] == 'robot':
                self.w.DestroyBody(model.turret)
                #del self.robots[model.name]
            #print 's1', self.v.sprites
            #print 'destroying', id(body)
            self.w.DestroyBody(body)
            #print 'destroyed', id(body)




    def make_testrobots(self):
        self.makerobot('R1', (4, 0), pi)
        self.makerobot('R2', (-4, 0), 0)
        self.makerobot('R3', (0, 4), pi)
        self.makerobot('R4', (0, -4), 0)

        self.makerobot('R5', (4, 4), pi)
        self.makerobot('R6', (-4, 4), 0)
        self.makerobot('R7', (-4, -4), pi)
        self.makerobot('R8', (4, -4), 0)

        self.makerobot('R1')
        self.makerobot('R2')
        self.makerobot('R3')
        self.makerobot('R4')

        self.makerobot('R5')
        self.makerobot('R6')
        self.makerobot('R7')
        self.makerobot('R8')

    def testmoves(self):
        self.count -= 1
        if self.count < 0:
            self.force = -self.force
            self.count = 1000

        for name, robot in self.robots.items():
            r = robot.body
            pos = r.position
            vel = r.linearVelocity

            #print 'pos', pos
            #print dir(vel)

            localforce = box2d.b2Vec2(self.force, 0)
            worldforce = r.GetWorldVector(localforce)

            r.ApplyForce(worldforce, pos)

            #if r.angularVelocity < .5:
                #r.ApplyTorque(.5)
            #else:
                #print 'av', r.angle

            r.ApplyTorque(4)

            bullet = random.randrange(3)
            if bullet == 2:
                #print name, 'shoots'
                self.makebullet(name)

    def to_dict(self):
        bullets = [b.to_dict() for b in self.bullets]
        robots = [r.to_dict() for r in self.robots.values()]
        sprites = [s.to_dict() for s in self.sprites]
        walls = [w.to_dict() for w in self.walls]
        worldDict = {
                'bullets': bullets,
                'robots': robots,
                'sprites': sprites,
                'walls': walls,
                }
        return worldDict

class CL(box2d.b2ContactListener):
    def Result(self, result):
        s1 = result.shape1
        b1 = s1.GetBody()
        actor1 = b1.userData['actor']
        kind1 = b1.userData.get('kind', None)

        s2 = result.shape2
        b2 = s2.GetBody()
        actor2 = b2.userData['actor']
        kind2 = b2.userData.get('kind', None)

        dmg = 0
        hitdmg = conf.direct_hit_damage
        cds = conf.collision_damage_start
        cdf = conf.collision_damage_factor
        nimpulse = result.normalImpulse
        timpulse = result.tangentImpulse
        impulse = box2d.b2Vec2(nimpulse, timpulse).Length()
        coldmg = int((cdf * (impulse - cds))**2) + 1

        if kind2=='robot':
            if kind1=='bullet':
                ring = s1.userData.get('ring', None)
                shooter = b1.userData['shooter']
                if ring is None and shooter == actor2:
                    #can't shoot yourself
                    pass
                elif ring is None:
                    dmg = hitdmg
                    print 'Robot', actor2.name, 'shot for', dmg,
                else:
                    hits = s1.userData['hits']
                    if actor2 not in hits[ring]:
                        dmg = conf.explosion_damage[ring]
                        print 'Robot', actor2.name, 'in blast area for', dmg
                        hits[ring].append(actor2)
                    else:
                        pass
                        #print actor2.name, 'already hit by ring', ring
            else:
                shooter = None
                if impulse > cds:
                    dmg = coldmg
                    print 'Robot', actor2.name, 'coll for', dmg,

            if dmg:
                actor2.health -= dmg
                if shooter is not None:
                    shooter._damage_caused += dmg
                actor2.i.health.step(dmg)
                if actor2.health <= 0:
                    actor2.alive = False
                    if conf.remove_dead_robots:
                        if actor2 not in self.w.to_destroy:
                            self.w.to_destroy.append(actor2)
                    print
                else:
                    print 'down to', actor2.health

        if kind1=='robot':
            if kind2=='bullet':
                ring = s2.userData.get('ring', None)
                shooter = b2.userData['shooter']
                if ring is None and shooter == actor1:
                    #can't shoot yourself
                    pass
                elif ring is None:
                    dmg = hitdmg
                    print 'Robot', actor1.name, 'shot for', dmg,
                else:
                    hits = s2.userData['hits']
                    if actor1 not in hits[ring]:
                        dmg = conf.explosion_damage[ring]
                        print 'Robot', actor1.name, 'in blast area for', dmg
                        hits[ring].append(actor1)
                    else:
                        pass
                        #print actor1.name, 'already hit by ring', ring
            else:
                shooter = None
                if impulse > cds:
                    dmg = coldmg
                    print 'Robot', actor1.name, 'coll for', dmg,

            if dmg:
                actor1.health -= dmg
                if shooter is not None:
                    shooter._damage_caused += dmg
                actor1.i.health.step(dmg)
                if actor1.health <= 0:
                    actor1.alive = False
                    if conf.remove_dead_robots:
                        if actor1 not in self.w.to_destroy:
                            self.w.to_destroy.append(actor1)
                    print
                else:
                    print 'down to', actor1.health

        if actor1 in self.w.bullets and not actor1._exploding:
            if actor1 not in self.w.to_destroy:
                self.w.to_destroy.append(actor1)

        if actor2 in self.w.bullets and not actor2._exploding:
            if actor2 not in self.w.to_destroy:
                self.w.to_destroy.append(actor2)



if __name__ == '__main__':
    w = World()
    cl = CL()
    w.w.SetContactListener(cl)
    cl.w = w
    while not w.v.quit:
        w.step()
