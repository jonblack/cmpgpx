#!/usr/bin/env python3

import argparse
import logging
import math
import os

logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(message)s', level=logging.INFO)
_log = logging.getLogger(__name__)
logging.getLogger('geotiler').setLevel(logging.INFO)
logging.getLogger('geotiler.map').setLevel(logging.INFO)
logging.getLogger('geotiler.tilenet').setLevel(logging.INFO)

import cairocffi as cairo
import geotiler
import gpxpy
import numpy

import geo
import gfx


def align_tracks(track1, track2, gap_penalty):
    """ Needleman-Wunsch algorithm adapted for gps tracks. """

    _log.info("Aligning tracks")

    def similarity(p1, p2):
        d = gpxpy.geo.distance(p1.latitude, p1.longitude, p1.elevation,
                               p2.latitude, p2.longitude, p2.elevation)
        return -d

    # construct f-matrix
    f = numpy.zeros((len(track1), len(track2)))
    for i in range(0, len(track1)):
        f[i][0] = gap_penalty * i
    for j in range(0, len(track2)):
        f[0][j] = gap_penalty * j
    for i in range(1, len(track1)):
        t1 = track1[i]
        for j in range(1, len(track2)):
            t2 = track2[j]
            match = f[i-1][j-1] + similarity(t1, t2)
            delete = f[i-1][j] + gap_penalty
            insert = f[i][j-1] + gap_penalty
            f[i, j] = max(match, max(delete, insert))

    # backtrack to create alignment
    a1 = []
    a2 = []
    i = len(track1) - 1
    j = len(track2) - 1
    while i > 0 or j > 0:
        if i > 0 and j > 0 and \
           f[i, j] == f[i-1][j-1] + similarity(track1[i], track2[j]):
            a1.insert(0, track1[i])
            a2.insert(0, track2[j])
            i -= 1
            j -= 1
        elif i > 0 and f[i][j] == f[i-1][j] + gap_penalty:
            a1.insert(0, track1[i])
            a2.insert(0, None)
            i -= 1
        elif j > 0 and f[i][j] == f[i][j-1] + gap_penalty:
            a1.insert(0, None)
            a2.insert(0, track2[j])
            j -= 1
    return a1, a2


def draw_alignment(track1, track2, bounds):
    """ Draws the aligned tracks with the given bounds onto a cairo surface. """

    _log.info("Drawing alignment")

    mm = geotiler.Map(extent=bounds, zoom=14)
    width, height = mm.size
    image = geotiler.render_map(mm)

    # create cairo surface
    buff = bytearray(image.convert('RGBA').tobytes('raw', 'BGRA'))
    surface = cairo.ImageSurface.create_for_data(
        buff, cairo.FORMAT_ARGB32, width, height)
    cr = cairo.Context(surface)

    a1_l = len(track1)
    a2_l = len(track2)
    assert a1_l == a2_l
    p_radius = 2
    for i in range(0, a1_l):
        if a1[i] is not None and a2[i] is not None:
            cr.set_source_rgba(0.2, 0.7, 1.0, 1.0)
            a1_x, a1_y = mm.rev_geocode((a1[i].longitude, a1[i].latitude))
            cr.arc(a1_x, a1_y, p_radius, 0, 2 * math.pi)
            cr.fill()
            cr.set_source_rgba(0.0, 0.0, 1.0, 1.0)
            a2_x, a2_y = mm.rev_geocode((a2[i].longitude, a2[i].latitude))
            cr.arc(a2_x, a2_y, p_radius, 0, 2 * math.pi)
            cr.fill()
        elif a1[i] is not None and a2[i] is None:
            cr.set_source_rgba(1.0, 0.0, 0.0, 1.0)
            a1_x, a1_y = mm.rev_geocode((a1[i].longitude, a1[i].latitude))
            cr.arc(a1_x, a1_y, p_radius, 0, 2 * math.pi)
            cr.fill()
        elif a1[i] is None and a2[i] is not None:
            cr.set_source_rgba(1.0, 0.5, 0.0, 1.0)
            a2_x, a2_y = mm.rev_geocode((a2[i].longitude, a2[i].latitude))
            cr.arc(a2_x, a2_y, p_radius, 0, 2 * math.pi)
            cr.fill()
    return surface


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('gpx_file1', type=argparse.FileType('r'))
    parser.add_argument('gpx_file2', type=argparse.FileType('r'))
    parser.add_argument('-c', '--cutoff', type=int, default=10,
                        help="cutoff distance in meters for similar points")
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-e', '--even', type=int,
                        help="evenly distribute points in meters")
    parser.add_argument('-o', '--output-file', default="alignment.png",
                        help="output filename")
    parser.add_argument('-s', '--separate_tracks', action='store_true',
                        help="output original tracks to separate images")
    args = parser.parse_args()

    if args.debug:
        _log.setLevel(logging.DEBUG)
        logging.getLogger('geotiler.tilenet').setLevel(logging.DEBUG)

    gpx1 = gpxpy.parse(args.gpx_file1)
    gpx2 = gpxpy.parse(args.gpx_file2)
    gap_penalty = -args.cutoff

    # Join all the points from all segments for the track into a single list
    gpx1_points = [p for s in gpx1.tracks[0].segments for p in s.points]
    gpx2_points = [p for s in gpx2.tracks[0].segments for p in s.points]

    # Evenly distribute the points
    if args.even:
        gpx1_points = geo.interpolate_distance(gpx1_points, args.even)
        gpx2_points = geo.interpolate_distance(gpx2_points, args.even)

    # Run the alignment
    a1, a2 = align_tracks(gpx1_points, gpx2_points, gap_penalty)

    # Calculate map bounding box with padding
    padding_pct = 10
    bounds1 = gpx1.get_bounds()
    bounds2 = gpx2.get_bounds()
    bbox1 = gfx.add_padding((bounds1.min_longitude, bounds1.min_latitude,
                             bounds1.max_longitude, bounds1.max_latitude), 10)
    bbox2 = gfx.add_padding((bounds2.min_longitude, bounds2.min_latitude,
                             bounds2.max_longitude, bounds2.max_latitude), 10)
    bbox = (min(bbox1[0], bbox2[0]), min(bbox1[1], bbox2[1]),
            max(bbox1[2], bbox2[2]), max(bbox1[3], bbox2[3]))

    # Draw tracks and alignment
    if args.separate_tracks:
        gpx1_surface = gfx.draw_track(gpx1_points, bbox1)
        gpx1_img_filename = "{}.png".format(
            os.path.basename(os.path.splitext(args.gpx_file1.name)[0]))
        _log.info("Saving original track to '{}'".format(gpx1_img_filename))
        gpx1_surface.write_to_png(gpx1_img_filename)

        gpx2_surface = gfx.draw_track(gpx2_points, bbox2)
        gpx2_img_filename = "{}.png".format(
            os.path.basename(os.path.splitext(args.gpx_file2.name)[0]))
        _log.info("Saving original track to '{}'".format(gpx2_img_filename))
        gpx2_surface.write_to_png(gpx2_img_filename)

    surface = draw_alignment(a1, a2, bbox)
    _log.info("Saving alignment to '{}'".format(args.output_file))
    surface.write_to_png(args.output_file)

    # Output the difference in the tracks as a percentage
    match = 0
    for i in range(0, len(a1)):
        if a1[i] is not None and a2[i] is not None:
            match += 1
    total_similar = match / len(a1)
    _log.info("Track Similarity: {:.2%}".format(total_similar))
