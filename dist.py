#!/usr/bin/env python3

import argparse
import copy
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('gpx_file', type=argparse.FileType('r'))
    parser.add_argument('even', type=int, default=20)
    parser.add_argument('-d', '--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        _log.setLevel(logging.DEBUG)
        logging.getLogger('geotiler.tilenet').setLevel(logging.DEBUG)

    gpx = gpxpy.parse(args.gpx_file)

    # Join all the points from all segments for the track into a single list
    gpx_points = [p for s in gpx.tracks[0].segments for p in s.points]

    # Calculate map bounding box with padding
    padding_pct = 10
    bounds = gpx.get_bounds()
    bbox = gfx.add_padding((bounds.min_longitude, bounds.min_latitude,
                            bounds.max_longitude, bounds.max_latitude), 10)

    # Draw the original track
    gpx_surface = gfx.draw_track(gpx_points, bbox)
    gpx_img_filename = "original.png"
    _log.info("Saving original track to '{}'".format(gpx_img_filename))
    gpx_surface.write_to_png(gpx_img_filename)

    # Evenly distribute the points
    gpx_points = geo.interpolate_distance(gpx_points, args.even)

    # Draw the distributed track
    gpx_surface = gfx.draw_track(gpx_points, bbox)
    gpx_img_filename = "even.png"
    _log.info("Saving original track to '{}'".format(gpx_img_filename))
    gpx_surface.write_to_png(gpx_img_filename)
