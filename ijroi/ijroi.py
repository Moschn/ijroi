# Copyright: Luis Pedro Coelho <luis@luispedro.org>, 2012
#            Tim D. Smith <git@tim-smith.us>, 2015
# License: MIT

import numpy as np


def read_roi(fileobj):
    '''
    points = read_roi(fileobj)

    Read ImageJ's ROI format
    '''
    # This is based on:
    # http://rsbweb.nih.gov/ij/developer/source/ij/io/RoiDecoder.java.html
    # http://rsbweb.nih.gov/ij/developer/source/ij/io/RoiEncoder.java.html

    SPLINE_FIT = 1
    DOUBLE_HEADED = 2
    OUTLINE = 4
    OVERLAY_LABELS = 8
    OVERLAY_NAMES = 16
    OVERLAY_BACKGROUNDS = 32
    OVERLAY_BOLD = 64
    SUB_PIXEL_RESOLUTION = 128
    DRAW_OFFSET = 256

    class RoiType:
        POLYGON = 0
        RECT = 1
        OVAL = 2
        LINE = 3
        FREELINE = 4
        POLYLINE = 5
        NOROI = 6
        FREEHAND = 7
        TRACED = 8
        ANGLE = 9
        POINT = 10

    def get8():
        s = fileobj.read(1)
        if not s:
            raise IOError('readroi: Unexpected EOF')
        return ord(s)

    def get16():
        b0 = get8()
        b1 = get8()
        return (b0 << 8) | b1

    def get32():
        s0 = get16()
        s1 = get16()
        return (s0 << 16) | s1

    def getfloat():
        v = np.int32(get32())
        return v.view(np.float32)

    magic = fileobj.read(4)
    if magic != b'Iout':
        raise IOError('Magic number not found')
    version = get16()

    # It seems that the roi type field occupies 2 Bytes, but only one is used
    roi_type = get8()
    # Discard second Byte:
    get8()

    if roi_type not in [RoiType.FREEHAND, RoiType.RECT]:
        raise ValueError('roireader: ROI type %s not supported' % roi_type)

    top = get16()
    left = get16()
    bottom = get16()
    right = get16()
    n_coordinates = get16()
    x1 = getfloat()
    y1 = getfloat()
    x2 = getfloat()
    y2 = getfloat()
    stroke_width = get16()
    shape_roi_size = get32()
    stroke_color = get32()
    fill_color = get32()
    subtype = get16()
    if subtype != 0:
        raise ValueError('roireader: ROI subtype %s not supported (!= 0)' % subtype)
    options = get16()
    arrow_style = get8()
    arrow_head_size = get8()
    rect_arc_size = get16()
    position = get32()
    header2offset = get32()

    if roi_type == RoiType.RECT:
        if options & SUB_PIXEL_RESOLUTION:
            return np.array(
                [[x1, y1], [x1+x2, y1], [x1+x2, y1+y2], [x1, y1+y2]],
                dtype=np.float32)
        else:
            return np.array(
                [[left, top], [right, top], [right, bottom], [left, bottom]],
                dtype=np.int16)

    if options & SUB_PIXEL_RESOLUTION:
        getc = getfloat
        points = np.empty((n_coordinates, 2), dtype=np.float32)
        fileobj.seek(4*n_coordinates, 1)
    else:
        getc = get16
        points = np.empty((n_coordinates, 2), dtype=np.int16)

    points[:, 1] = [getc() for i in range(n_coordinates)]
    points[:, 0] = [getc() for i in range(n_coordinates)]

    if options & SUB_PIXEL_RESOLUTION == 0:
        points[:, 1] += left
        points[:, 0] += top
        points -= 1

    return points


def read_roi_zip(fname):
    import zipfile
    with zipfile.ZipFile(fname) as zf:
        return [read_roi(zf.open(n)) for n in zf.namelist()]