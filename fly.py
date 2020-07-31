from utils import Calculator
from classes import Type, Location, Coords
from math import cos, sin, radians, atan2, degrees, asin, pi, sqrt
import matplotlib.pyplot as plt

def main():
    """
    creates an environment and a medium range missile (mrm) as well as two platforms, F-35 and SA-X.
    Sets their starting location and altitude, etc of F-35
    sets the intent of the SAM to target 'p' (the F-35) and shoot it...
    adds both to 'platforms'
    and then executes
    """
    e = Environment()

    mrm = Missile(2.5, 50)

    f35 = Type(mrm, 7, 3)
    saX = Type(mrm, 1, 0)

    p_coords = Coords(35, -115)
    p_location = Location(p_coords, 30000, 280, 1, 0)
    p = Platform(f35, "F-35_1", p_location)

    adv_coords = Coords(36, -117)
    adv_location = Location(adv_coords, 0, 0, 0)
    adv = Platform(saX, "SA-X_1", adv_location)
    adv.intent["target"] = (p, "Offensive")
    adv.intent["master_arm"] = "on"

    e.platforms.append(p)
    e.platforms.append(adv)
    e.execute()


class Environment:

    #these are just for the shitty matplotlib plot
    lat_data = []
    long_data = []

    def __init__(self):
        self.time = 0  #datetime
        self.platforms = []

    def check_for_deaths(self):
        """
        checks every platform to see if it 'hits' another platform
        the 'immunities' property ensures a doesn't kill it's own shooter immediately after launch
        """
        for plat_a in self.platforms:
            for plat_b in [plat for plat in self.platforms if plat != plat_a]:
                if plat_a.is_impacting(plat_b):
                    if plat_a not in plat_b.immunities and plat_b not in plat_a.immunities:
                        plat_a.die(self)
                        plat_b.die(self)

    def execute(self):
        """
        just runs step() for each platform and checks_for_death after each step
        also shit plot
        """
        while self.time < 10000:
            while len(self.platforms) > 1:
                for platform in self.platforms:
                    platform.step(self)
                self.time += 1
                self.check_for_deaths()

            fig = plt.figure()
            ax = fig.add_subplot(111)
            ax.scatter(self.long_data, self.lat_data)
            plt.show()

class Platform:

    c = Calculator()

    def __init__(self, type, label, location):
        self.immunities = []
        self.type = type
        self.location = location
        self.label = label
        self.g = 1
        self.intent = {
            "hdg":location.hdg,
            "alt":location.alt,
            "target":(None,None),
            "master_arm": "off",
        }

    def __repr__(self):
        return f"{self.label}"

    def die(self, env):
        print(f"{self.label} died")
        env.platforms.remove(self)

    def is_impacting(self, other):
        if self.get_range_to(other) < 0.5:
            return True
        else:
            return False

    def get_bearing_to(self, target):
        my = self.location.coords
        his = target.location.coords
        X = cos(his.lat)*sin(his.lon-my.lon)
        Y = cos(my.lat)*sin(his.lat) - sin(my.lat)*cos(his.lat)*cos(his.lon-my.lon)
        rads = atan2(X,Y)
        az = (rads*180)/pi
        if az < 0: return 360+az
        else:
            return az

    def get_range_to(self, target):
        r = 3440.1 #radius of earth in nm
        tgt_coords = target.location.coords
        own_coords = self.location.coords
        deltaLat = tgt_coords.lat - own_coords.lat
        deltaLong = tgt_coords.lon - own_coords.lon
        a = sin(deltaLat / 2)**2 + cos(own_coords.lat) * cos(tgt_coords.lat) * sin (deltaLong/2)**2
        c = 2 * asin(sqrt(a))
        return c*r

    def turn(self, hdg, dive=0):
        st_hdg = self.location.hdg
        if abs(st_hdg-hdg) > 15:  # this needs to get better.
            if self.g < self.type.max_g:
                self.g += self.type.g_onset_rate
            if st_hdg < 180:
                if st_hdg < hdg < st_hdg + 180:
                    self.location.hdg += self.c.g_performance(self.location.vel, self.g)[0]
                else:
                    self.location.hdg -= self.c.g_performance(self.location.vel, self.g)[0]
            else:
                if st_hdg - 180 < hdg < self.location.hdg:
                    self.location.hdg -= self.c.g_performance(self.location.vel, self.g)[0]
                else:
                    self.location.hdg += self.c.g_performance(self.location.vel, self.g)[0]
        else:
            self.location.hdg = hdg

        # correct for 360 degrees...
        if self.location.hdg < 0:
            self.location.hdg += 360
        if self.location.hdg > 360:
            self.location.hdg -= 360

    def move(self):
        r = 20.902e6  # radius of earth in feet
        brg = radians(self.location.hdg)
        dist = self.c.airspeed_convert(self.location.vel, self.location.alt) * 1.68781  # fps
        startLat = self.location.coords.lat
        startLong = self.location.coords.lon
        endLat = asin(sin(startLat)*cos(dist/r) + cos(startLat)*sin(dist/r)*cos(brg))
        endLong = startLong + atan2(sin(brg)*sin(dist/r)*cos(startLat),cos(dist/r)-sin(startLat)*sin(endLat))
        endCoords = Coords(degrees(endLat),degrees(endLong))
        self.location.coords = endCoords

    def step(self, env):
        self.check_intent(env)
        self.turn(self.intent['hdg'])
        self.move()
        if env.time % 1 == 0:
            print(f"{self.label}, {self.location.coords}, {self.intent['hdg']}")

        #for shitty matplotlib:
        env.lat_data.append(self.location.coords.lat)
        env.long_data.append(self.location.coords.lon)

    def check_intent(self, env):
        """
        shoots the enemy if (a) targeted and (b) in range...
        if defending, tries to put the enemy on the tail
        """
        target = self.intent["target"][0]
        posture = self.intent["target"][1]
        if posture == "Offensive":
            self.intent['hdg'] = self.get_bearing_to(target)
            if self.intent['master_arm'] == "on":
                if self.get_range_to(target) < self.type.msl.max_range:
                    self.shoot(target, env)
        elif posture == "Defensive":
            self.intent['hdg'] = target.get_bearing_to(self)

    def shoot(self, target, env):
        missile = self.type.msl
        missile.fire(self, target, env.time)
        env.platforms.append(missile)
        # target.intent["target"] = (missile, "Defensive")  #  uncomment this to have fighter defend
        print("SHOOOOOOOOOOOOOT")



class Missile(Platform):
    def __init__(self, speed, max_range):
        self.immunities = []
        self.speed = speed
        self.max_range = max_range
        self.g = 1
        self.type = Type(None, 20, 15)
        # super.__init__(None, "msl", None)

    def fire(self, shooter, target, hack):

        #don't kill self with own missile (since it'll trigger 'check_for_death')
        self.immunities.append(shooter)
        shooter.immunities.append(self)

        shooter.intent["master_arm"] = "off"
        self.location = Location(shooter.location.coords, shooter.location.alt, shooter.location.hdg, self.speed)
        self.label = f"msl{hack}"
        self.target = target
        self.intent = {
            "hdg":self.get_bearing_to(self.target),
            "alt":self.location.alt,
            "target":(self.target, "Offensive"),
            "master_arm":"off"
        }

if __name__ == '__main__':
    main()
