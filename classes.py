from utils import Calculator
from math import cos, sin, radians, atan2, degrees, asin, pi, sqrt

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
