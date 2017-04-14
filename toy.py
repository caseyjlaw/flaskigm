from flask import Flask
from astropy.coordinates import SkyCoord
from astropy.utils.exceptions import AstropyWarning
from astropy import units as u
from ne2001 import density
from SM2017 import SM
from astroquery.simbad import Simbad
import warnings
warnings.simplefilter('ignore', category=AstropyWarning)

app = Flask(__name__)
ed = density.ElectronDensity()
simbad = Simbad()

@app.route("/")
def hello():
    return "ne2001 and sm2017 server"

@app.route("/ne2001/l<int:l>b<int:b>d<int:d>")
def ne2001(l, b, d):
    dm = ed.DM(l, b, d).value
    return "DM={0}".format(dm)

@app.route("/coord/name<string:name>")
def coord(name):
    tab = simbad.query_object(name)
    if tab:
        namecol = tab.colnames.index("MAIN_ID")
        racol = tab.colnames.index("RA")
        deccol = tab.colnames.index("DEC")
        if len(tab) == 1:
            retname = tab[0][namecol]
            radec = '{0}, {1}'.format(tab[0][racol], tab[0][deccol])
            return "{0} is at {1}".format(retname, radec)
        else:
            column = tab.columns[namecol]
            retname = ', '.join([name for name in column])
            return "Query {0} returns {1} names: {2}".format(name, len(tab), retname)
    else:
        return "Query {0} returns nothing.".format(name)

@app.route("/sm2017/l<int:l>b<int:b>")
def sm2017(l, b):
    nu = 1.4e9
    frame = 'galactic'
    pos = SkyCoord([l]*u.degree, [b]*u.degree, frame=frame)
    sm = SM('/Users/caseyjlaw/code/SM2017/data/Halpha_map.fits', nu=nu)
    return "SM={0}".format(sm.get_halpha(pos))

if __name__ == "__main__":
    app.run()
