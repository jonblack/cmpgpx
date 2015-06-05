import copy
import logging
import math

import gpxpy

_log = logging.getLogger(__name__)


def bearing(point1, point2):
    """
    Calculates the initial bearing between point1 and point2 relative to north
    (zero degrees).
    """

    lat1r = math.radians(point1.latitude)
    lat2r = math.radians(point2.latitude)
    dlon = math.radians(point2.longitude - point1.longitude)

    y = math.sin(dlon) * math.cos(lat2r)
    x = math.cos(lat1r) * math.sin(lat2r) - math.sin(lat1r) \
                        * math.cos(lat2r) * math.cos(dlon)
    return math.degrees(math.atan2(y, x))


def interpolate_distance(points, distance):
    """
    Interpolates points so that the distance between each point is equal
    to `distance` in meters.

    Only latitude and longitude are interpolated; time and elavation are not
    interpolated and should not be relied upon.
    """
    # TODO: Interpolate elevation and time.

    _log.info("Distributing points evenly every {} meters".format(distance))

    d = 0
    i = 0
    even_points = []
    while i < len(points):
        if i == 0:
            even_points.append(points[0])
            i += 1
            continue

        if d == 0:
            p1 = even_points[-1]
        else:
            p1 = points[i-1]
        p2 = points[i]

        d += gpxpy.geo.distance(p1.latitude, p1.longitude, p1.elevation,
                                p2.latitude, p2.longitude, p2.elevation)

        if d >= distance:
            brng = bearing(p1, p2)
            ld = gpxpy.geo.LocationDelta(distance=-(d-distance), angle=brng)
            p2_copy = copy.deepcopy(p2)
            p2_copy.move(ld)
            even_points.append(p2_copy)

            d = 0
        else:
            i += 1
    else:
        even_points.append(points[-1])

    return even_points
