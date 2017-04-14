from math import pi, sin, cos, acos, ceil, modf
import numpy as np
import scipy as sp
from flask import Flask, render_template
from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, get_sun
from astropy.time import Time
import csv

app = Flask(__name__)

# GBO location by default
loc = EarthLocation(lat=38.4*u.deg, lon=-79.8*u.deg, height=808*u.m)

# times in PST (UTC - 8 hours)
pstutoffset = -8 * u.hour
utcmidnight = Time('2017-02-21 00:00:00')
pstmidnight = utcmidnight - pstutoffset

# 1 minute timesteps between midnight and midnight + 24 hours
delta_midnight = np.linspace(0, 24, 24*60)*u.hour
times = pstmidnight+delta_midnight

# elevation limit of the telescope (set ellim = 0 to calculate rise / set above horizon)
ellim = 5.

@app.route("/")
def hello():
    return "Rise / set calculator"

@app.route("/obs/ra<float:ra>de<float:de>")
def obs(ra,de):
    coord = SkyCoord(ra,de,unit='deg')
    altazframe = AltAz(obstime=times, location=loc)
    altazs = coord.transform_to(altazframe)
    alts = altazs.alt
    altz = alts.deg - ellim
    riseset = delta_midnight[sp.where(altz[:-1] * altz[1:] < 0)]
    return str(riseset)

class Pagination(object):

    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

PER_PAGE = 20

@app.route('/pulsars/riseset/', defaults={'page': 0})
@app.route("/pulsars/riseset/page/<int:page>")
def showpulsars(page):
    pulsar_names = []
    pulsar_rajd = []
    pulsar_decjd = []
    pulsar_risesetlst = []
    with open("psrcat.csv", "r") as csvfile:
        pulsars = csv.reader(csvfile, delimiter=",")
	p = list(pulsars)
	count = len(p)
	for i in range(page*PER_PAGE, (page + 1)*PER_PAGE):
            pulsar_names.append(p[i][0])
            pulsar_rajd.append(p[i][1])
            pulsar_decjd.append(p[i][2])
            pulsar_risesetlst.append(calc_rise_set(float(p[i][1]),
                float(p[i][2]), 38.4,
                -79.8, 85.0))
        num_pulsars = len(pulsar_names)
	pagination = Pagination(page, PER_PAGE, count)
        return render_template("pulsars.html", pagination=pagination, n=num_pulsars, names=pulsar_names,
                rajd=pulsar_rajd, decjd=pulsar_decjd,
                risesetlst=pulsar_risesetlst)

def calc_rise_set(ra, dec, lat, long, maxza):
    obsLat = lat                # latitude in degrees
    obsMaxZA = maxza            # max ZA in degrees
    obsMinEl = (90.0 - obsMaxZA)                    # min elevation in degrees

    # check if the object never rises or never sets
    if obsLat >= 0:
        obsRangeMin = -90 + obsLat + obsMinEl
        obsRangeMax = obsLat + 90 - obsMinEl
        if (dec < obsRangeMin) or (dec > obsRangeMax):
            return ["Never visible"]
        elif obsRangeMax > 90:
            if dec > 90 - obsLat + obsMinEl:
                return ["Always visible"]
    else:
        obsRangeMin = 90 + obsLat - obsMinEl
        obsRangeMax = obsLat - 90 + obsMinEl
        if (dec > obsRangeMin) or (dec < obsRangeMax):
            return ["Never visible"]
        elif obsRangeMax < -90:
            if dec < -90 - obsLat - obsMinEl:
                return ["Always visible"]

    decRad = dec * pi / 180
    obsMinEl = obsMinEl * pi / 180
    obsLat = obsLat * pi / 180
    cosHA = (sin(obsMinEl) - sin(decRad) * sin(obsLat))                       \
            / (cos(decRad) * cos(obsLat))
    haRiseSet = acos(cosHA) * 180.0 / pi       # in degrees
    lstRise = ra - haRiseSet                        # in degrees
    lstSet = ra + haRiseSet                         # in degrees
    lstRiseHour = int(modf(lstRise * 24 / 360)[1])
    lstRiseMin = int(round(modf(lstRise * 24 / 360)[0] * 60, 1))
    if lstRise < 0.0:
        lstRiseHour = 24 + lstRiseHour - 1
        lstRiseMin = 60 + lstRiseMin
    lstRiseStr = str(lstRiseHour).zfill(2) + ":" + str(lstRiseMin).zfill(2)
    lstSetHour = int(modf(lstSet * 24 / 360)[1])
    lstSetMin = int(round(modf(lstSet * 24 / 360)[0] * 60, 1))
    if lstSet >= 360.0:
        lstSetHour = lstSetHour - 24
    lstSetStr = str(lstSetHour).zfill(2) + ":" + str(lstSetMin).zfill(2)
    return [lstRiseStr, lstSetStr]

if __name__ == "__main__":
    app.run()
