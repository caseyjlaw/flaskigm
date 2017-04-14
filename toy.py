from flask import Flask, render_template, request
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
def landing():
    return render_template('landing.html', name="name, ne2001, and sm2017 server")


@app.route("/sm2017")
def landingsm2017():
    return render_template('landing.html', name="sm2017 server: enter l, b")


@app.route("/processne2001", methods=["POST"])
def getthree():
    l = float(request.form.get("l", "0."))
    b = float(request.form.get("b", "90."))
    d = float(request.form.get("d", "100"))
    dm = float(ed.DM(l, b, d).value)
    return render_template("ne2001form.html", name="Enter l, b, d for NE2001 calculation", dm=dm)
#    return "DM={0} pc/cm3".format(dm)

@app.route("/ne2001")
def ne2001landing():
    return render_template("ne2001form.html", name="Enter l, b, d for NE2001 calculation")


@app.route("/processcoord", methods=["POST"])
def getone():
    name = request.form.get("name")
    tab = simbad.query_object(name)
    if tab:
        namecol = tab.colnames.index("MAIN_ID")
        racol = tab.colnames.index("RA")
        deccol = tab.colnames.index("DEC")
        if len(tab) == 1:
            retname = tab[0][namecol]
            ra = tab[0][racol]
            dec = tab[0][deccol]
            return render_template("coordform.html", name=name, ra=ra, dec=dec)
        else:
            return render_template("coordform.html", name="Too many sources")

    return render_template("coordform.html", name="Not enough sources")


@app.route("/coord")
def coordlanding():
    return render_template("coordform.html", name="Enter source name")


#@app.route("/ne200l/l<int:l>b<int:b>d<int:d>")
#def ne2001(l, b, d):
#    dm = ed.DM(l, b, d).value
#    return render_template('ne2001.html', l=l, b=b, d=d, dm=dm)

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

@app.route('/obs/')
def obslookup():
    return render_template('obslookup.html')

@app.route('/geocode/')
def geocode():
    address = request.form.get("loc", "Arecibo")
    api_key = os.getenv("MAPS_API_KEY")
    if api_key == "":
        sys.exit("Please obtain an API key from https://developers.google.com/maps/documentation/geocoding/start#get-a-key and set the environment variable MAPS_API_KEY")

    #print api_key

    url = 'https://maps.googleapis.com/maps/api/geocode/json?'
    values = {'address' : address,
              'key' : api_key }

    data = urllib.urlencode(values)
    full_url = url + data
    #print full_url
    response = urllib2.urlopen(full_url)
    json_response = response.read()

    data_dict = json.loads(json_response)

    #print data_dict

    lat = data_dict['results'][0]['geometry']['location']['lat']
    lng = data_dict['results'][0]['geometry']['location']['lng']

    print lat, lng
    return [lat, lng]


@app.route('/pulsars/riseset/lat<float:lat>lng<float:lng>/', defaults={'page': 0})
@app.route("/pulsars/riseset/lat<float:lat>lng<float:lng>/page/<int:page>")
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
                float(p[i][2]), lat, lng, 90.0))
        num_pulsars = len(pulsar_names)
	pagination = Pagination(page, PER_PAGE, count)
        return render_template("pulsars.html", pagination=pagination, n=num_pulsars, names=pulsar_names,
                rajd=pulsar_rajd, decjd=pulsar_decjd,
                risesetlst=pulsar_risesetlst)

def calc_rise_set(ra, dec, lat, lng, maxza):
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
