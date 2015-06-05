import logging
import math

_log = logging.getLogger(__name__)

import cairocffi as cairo
import geotiler


def draw_track(track, bounds):
    """ Draws the given tracks with the given bounds onto a cairo surface. """

    _log.info("Drawing track")

    mm = geotiler.Map(extent=bounds, zoom=14)
    width, height = mm.size
    image = geotiler.render_map(mm)

    # create cairo surface
    buff = bytearray(image.convert('RGBA').tobytes('raw', 'BGRA'))
    surface = cairo.ImageSurface.create_for_data(
        buff, cairo.FORMAT_ARGB32, width, height)
    cr = cairo.Context(surface)

    p_radius = 2
    for p in track:
        cr.set_source_rgba(0.0, 0.0, 1.0, 1.0)
        a1_x, a1_y = mm.rev_geocode((p.longitude, p.latitude))
        cr.arc(a1_x, a1_y, p_radius, 0, 2 * math.pi)
        cr.fill()
    return surface


def add_padding(bbox, padding_pct):
    """ Add the given percentage padding to the given bounding box. """

    min_lat = bbox[1]
    max_lat = bbox[3]
    min_lon = bbox[0]
    max_lon = bbox[2]

    lat_pad = ((max_lat - min_lat) / 100) * padding_pct
    lon_pad = ((max_lon - min_lon) / 100) * padding_pct

    bbox = (min_lon - lon_pad, min_lat - lat_pad,
            max_lon + lon_pad, max_lat + lat_pad)

    return bbox
