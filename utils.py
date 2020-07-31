from math import tan, cos, acos, sin, degrees, radians, sqrt
# constants

class Missile:
    def __init__(self, accel_prof, max_rng=None):
        self.accel_prof = accel_prof
        self.max_rng = max_rng

    # def tti(self, launch_range):
    #     accel = {0: 0.5, 5: 1.5, 10: 3, 20: 2, 30: 1.5}
    #     t = 0
    #     rng = launch_range
    #     while rng > 0:
    #         try:
    #             speed = accel[t]
    #         rng += speed / 60
    #         t++
    #     return t # no this won't work....need input launch range and current range?  or time? shi.....

class Calculator:

    def __init__(self):
        self.onset_rate = 3

    # convert mach to true airspeed in knots
    def airspeed_convert(self, mach, alt):
        oat = (15 - (2*alt/1000))+273.15
        a_o = 661.47
        t_o = 288.15
        tas = a_o * mach * sqrt(oat/t_o)
        return tas

       # get radius in feet
    def level_turn_radius(self, velocity, bank):
        try:
            return velocity**2 / (11.26 * tan(radians(bank)))
        except:
            return 0

    # get degrees per second
    def level_turn_rate(self, velocity, bank):
        if velocity > 0:
            return (1091 * tan(radians(bank)))/velocity
        else:
            return 30

    # get g loading for level turn
    def level_turn_g(self, bank):
        return 1 / cos(radians(bank))

    # get bank based on g (level turn)
    def bank_for_g(self, g):
        return degrees(acos(1/g))

    def g_performance(self, vel, g):
        bank = self.bank_for_g(g)
        rate = self.level_turn_rate(vel, bank)
        radius = self.level_turn_radius(vel, bank)
        return (rate, radius)

    def time_to_act(self, time, vel):
        time = time  # how long it takes to react
        rng = 0
        for _ in range(time):
            rng += vel*1.8781
            time+=1
        return {'time': time, 'alt': 0, 'rng': -rng}

    def first_90(self, vel, g, dive=0):
        turn = 0
        rng = 0
        curr_g = 1
        time = 0
        alt = 0
        while turn < 90:
            curr_g = min(curr_g + self.onset_rate, g)
            rate = self.g_performance(vel, curr_g + sin(radians(min(turn,dive))))[0]
            v_rate = sin(radians(min(turn,dive)))*vel*1.68781
            rng += cos(radians(turn)) * vel
            alt += v_rate
            turn += rate
            time += 1
        return {'time': time, 'alt': alt, 'rng': -rng}

    def second_90(self, vel, g, dive):
        time = 90 / self.g_performance(vel, g)[0]
        alt = sin(radians(dive))*self.g_performance(vel, g)[1]
        rng = cos(radians(dive))*self.g_performance(vel, g)[1]
        return {'time': time, 'alt': alt, 'rng': rng, 'dive': dive}

    def accel_in_dive(self, start_vel, end_vel, dive):
        # const accel rate of 50 knots per second
        accel_rate = 50
        time = (end_vel - start_vel) / accel_rate
        sin_dive = sin(radians(dive))
        cos_dive = cos(radians(dive))
        # get vertical descent rates in feet per second
        st_vert_rate = sin_dive*start_vel*1.68781  # knots to fps
        end_vert_rate = sin_dive*end_vel*1.68781
        # get horizontal travel rates in fps
        st_horiz_rate = cos_dive*start_vel*1.68781
        end_horiz_rate = cos_dive*end_vel*1.68781
        # calculate altitude lost during acceleration
        alt = (st_vert_rate * time) + \
              ((end_vert_rate * time)-(st_vert_rate*time))/2
        # calculate range delta during accel
        rng = (st_horiz_rate * time) + \
              ((end_horiz_rate * time)-(st_horiz_rate*time))/2
        return {'time': time, 'alt': alt, 'rng': rng, 'vel': end_vel}

    def straight_dive(self, vel, dive, st_alt):
        descent_rate = sin(radians(dive))*vel*1.68781
        alt_to_lose = st_alt - (dive/0.01)  # 1% dive angle
        time = alt_to_lose / descent_rate  # time in seconds until recov.
        rng = cos(radians(dive))*vel*1.68781*time
        return {'time': time, 'alt': alt_to_lose, 'rng': rng}

    def recover_to_level(self, vel, st_dive, st_alt):
        min_alt = 500  # break this hard code at some point
        alt = st_alt
        dive = st_dive
        time = 0
        rng = 0
        def des(x): return sin(radians(x))*vel*1.68781  # feet per second
        def rng_inc(x): return cos(radians(x))*vel*1.68781
        while alt > min_alt:
            dive = alt * 0.01
            alt -= des(dive)
            rng += rng_inc(dive)
            time += 1
        dive = 0
        return {'time': time, 'alt': st_alt - alt, 'rng': rng, 'dive': dive}
