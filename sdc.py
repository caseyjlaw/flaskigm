
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

@app.route("/pulsars/riseset")
def showpulsars():
    pulsar_names = []
    pulsar_rajd = []
    pulsar_decjd = []
    pulsar_risesetlst = []
    with open("psrcat_small.csv", "r") as csvfile:
        pulsars = csv.reader(csvfile, delimiter=",")
        for pulsar in pulsars:
            pulsar_names.append(pulsar[0])
            pulsar_rajd.append(pulsar[1])
            pulsar_decjd.append(pulsar[2])
            #pulsar_risesetlst.append("test")
            pulsar_risesetlst.append(obs(pulsar[1], pulsar[2]))
        num_pulsars = len(pulsar_names)
        return render_template("pulsars.html", n=num_pulsars, names=pulsar_names,
                rajd=pulsar_rajd, decjd=pulsar_decjd,
                risesetlst=pulsar_risesetlst)

if __name__ == "__main__":
    app.run()
