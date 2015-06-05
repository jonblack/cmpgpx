from gpxpy.geo import distance, Location
from nose.tools import eq_

import geo


def test_bearing():
    p1 = Location(52.3710, 4.9006)
    p2 = Location(51.8448, 5.8631)

    d = distance(p1.latitude, p1.longitude, None,
                 p2.latitude, p2.longitude, None)
    eq_(int(d), 88000)

    bearing = geo.bearing(p1, p2)
    eq_(bearing, 131.292906976903)
