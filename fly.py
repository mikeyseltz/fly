from utils import Calculator
from math import cos, sin, radians, atan2, degrees, asin, pi


"""
at every moment:
ENV:
- timestamp
- check for impacts
PLATFORMS:
- Location
- Vector
- G
- Intent
    - target vector (heading and dive)
    ...if vector != target Vector
            if g != max g:
                g += onset_rate
            else:
                delta location / Vector
    - target action (shoot X):
        if in_range and no missile_in_flight:
            shoot missile:
                - create platform (missile) with intent (intercept)
                    - losing cue -> kill platform.
"""

def main():
    e = Environment()

    f35 = Type("MRM", 7, 3)
    saX = Type("MRM", 1, 0)

    p_coords = Coords(36, -115)
    p_location = Location(p_coords, 30000, 270, 1, 0)
    p = Platform(f35, "F-35_1", p_location)

    adv_coords = Coords(36, -117)
    adv_location = Location(adv_coords, 0, 0, 0)
    adv = Platform(saX, "SA-X_1", adv_location)
    adv.intent["target"] = (p, "Offensive")

    e.platforms.append(p)
    e.platforms.append(adv)
    e.execute()


class Environment:

    def __init__(self):
        self.time = 0  #datetime
        self.platforms = []

    def check_for_deaths(self):
        deaths = []
        for plat_a in self.platforms:
            for plat_b in [plat for plat in self.platforms if plat != plat_a]:
                if plat_a.location.is_impacting(plat_b.location):
                    plat_a.die()
                    plat_b.die()
                    deaths.append(plat_a)
                    deaths.append(plat_b)
        for deadman in deaths:
            self.platforms.remove(deadman)

    def execute(self):
        while self.time < 500:
        # while len(self.platforms) > 0:
            for platform in self.platforms:
                platform.step(self)
            self.time += 1

class Platform:

    c = Calculator()

    def __init__(self, type, label, location):
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

    def die(self):
        print(f"{self.label} died")

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
        deltaLat = target.coords.lat - self.coords.lat
        deltaLong = target.coords.lon - self.coords.lon
        a = sin(deltaLat / 2)**2 + cos(self.coords.lat) * cos(target.coords.lat) * sin (deltaLong/2)**2
        c = 2 * asin(sqrt(a))
        return c*r

    # def target(self, target):
    # 	self.turn(self.get_bearing_to(target))

    def turn(self, hdg, dive=0):
        st_hdg = self.location.hdg
        if abs(st_hdg-hdg) > 5:
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
        print(f"{self.label}, {self.location.coords}, {self.intent['hdg']}")

    def check_intent(self, env):
        target = self.intent["target"][0]
        posture = self.intent["target"][1]
        if posture == "Offensive":
            self.intent['hdg'] = self.get_bearing_to(target)
            if self.intent['master_arm'] == "on":
                if self.get_range_to(target) < self.missile.max_range:
                    self.shoot(self.type.msl, target, env.time)
        elif posture == "Defensive":
            self.intent['hdg'] = target.get_bearing_to(self)

    def shoot(self, target, type_msl, hack):
        missile = Missile(self.label, self.location, type_msl, target, env.time)
        env.platforms.append(missile)
        print("SHOOOOOOOOOT")

class Type:
    def __init__(self, msl, max_g, g_onset_rate, accel_prof=None):
        self.msl = msl
        self.max_g = max_g
        self.g_onset_rate = g_onset_rate
        self.accel_prof = accel_prof


class Location:
    def __init__(self, coords, alt, hdg, vel, dive=0):
        self.coords = coords
        self.alt = alt
        self.hdg = hdg
        self.vel = vel
        self.dive = dive

    def is_impacting(self, other):
        if self.get_range_to(other) < 0.5:
            return True
        else:
            return False


class Coords:
    def __init__(self, lat: float, lon: float):
        self.latString = "{:.6f}".format(lat)
        self.longString = "{:.6f}".format(lon)
        self.lat = radians(lat)
        self.lon = radians(lon)

    def __repr__(self):
        if self.lon < 0:
            return "N " + self.latString + " W " + self.longString[1:] #get rid of the negative
        else:
            return "N " + self.latString + " E " + self.longString


class Missile(Platform):
    def __init__(self, shooter, location, type_msl, target, hack):
        if type_msl == "MRM":
            self.label = f"msl{hack}"
            self.shooter = shooter
            self.target = target
            self.speed = 2.5
            self.max_range = 50
        self.intent = {
            "hdg":self.get_bearing_to(self.target),
            "alt":location.alt,
            "target":(self.target, "Offensive"),
            "master_arm": "on",
        }


if __name__ == '__main__':
    main()
