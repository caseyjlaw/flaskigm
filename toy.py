from flask import Flask
from astropy.coordinates import SkyCoord
from astropy.utils.exceptions import AstropyWarning
from astropy import units as u
from ne2001 import density
from SM2017 import SM
import warnings
warnings.simplefilter('ignore', category=AstropyWarning)

app = Flask(__name__)
ed = density.ElectronDensity()

@app.route("/")
def hello():
    return "ne2001 and sm2017 server"

@app.route("/ne2001/l<int:l>b<int:b>d<int:d>")
def ne2001(l, b, d):
    dm = ed.DM(l, b, d).value
    return "DM={0}".format(dm)

@app.route("/sm2017/l<int:l>b<int:b>")
def sm2017(l, b):
    nu = 1.4e9
    frame = 'galactic'
    pos = SkyCoord([l]*u.degree, [b]*u.degree, frame=frame)
    sm = SM('/Users/caseyjlaw/code/SM2017/data/Halpha_map.fits', nu=nu)
    return "SM={0}".format(sm.get_halpha(pos))

if __name__ == "__main__":
    app.run()
