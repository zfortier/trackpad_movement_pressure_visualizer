#!/usr/bin/env python3
# pylint: disable=C0114

import sys
import os
import re
import numpy as np
import sympy as syp
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

EVENT_TYPE_PTRN = r'^#\s+Event\s+type\s+(\d+)\s+\(([^)]+)\)$'
EVENT_CODE_PTRN = r'^#\s+Event\s+code\s+(\d+)\s+\(([^)]+)\)$'
EVENT_PROP_PTRN = r'^#\s+(\w+)\s+([-\d]+)$'
VAL_LINE_PTRN = r'^\-\s+\[\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+\s*\]\s*#.*$'
VAL_PTRN = r'^-\s+(\[\s*-?\d+,\s*-?\d+,\s*-?\d+,\s*-?\d+,\s*-?\d+\s*\]).*'
POS_PRES_COLORS = [0.25, 0.4] 
NEG_PRES_COLORS = [0.75, 0.9] 
TRACKPAD_X_Y_PRESMAX = (8000, 6000, 255)
FIG_XY_DPI = (6, 6, 200)

def read_file():
    with open(sys.argv[1], 'r') as fin:
        lines = [x.strip() for x in fin.readlines()]
    while not re.match(EVENT_TYPE_PTRN, lines[0]):
        _ = lines.pop(0)
    return lines


def split_pop(lines, pattern, count):
    """
    given a pattern and count, checks if the first element in lines matches
    pattern and yields count elements when split. If it does, the line is
    removed and the elements are returned.
    """
    if (len(parts := re.split(pattern, lines[0])) - 2) == count:
        _ = lines.pop(0)
        return parts[1:-1]
    return [None] * count


def color(p, dpdt, max_p): # also try replacing `p` with `dpdt` below in the calculations
    if dpdt > 0:
        return POS_PRES_COLORS[0] + (p * (POS_PRES_COLORS[1] - POS_PRES_COLORS[0]) / max_p)
    elif dpdt < 0:
        return NEG_PRES_COLORS[0] + (p * (NEG_PRES_COLORS[1] - NEG_PRES_COLORS[0]) / max_p)
    return NEG_PRES_COLORS[0] - POS_PRES_COLORS[1]



def build_key_lookups(lines):
    event_type_lkup = {}
    event_code_lkup = {}
    event_props = {}
    while all(e_type := split_pop(lines, EVENT_TYPE_PTRN, 2)):
        event_type_lkup[int(e_type[0])] = e_type[1]
        while all(e_code := split_pop(lines, EVENT_CODE_PTRN, 2)):
            event_code_lkup[int(e_code[0])] = e_code[1]
            while all(e_prop := split_pop(lines, EVENT_PROP_PTRN, 2)):
                if not event_props.get(e_code[1]):
                    event_props[e_code[1]] = {}
                event_props[e_code[1]][e_prop[0]] = int(e_prop[1])
    return event_type_lkup, event_code_lkup, event_props

    
def parse_lines(lines):
    event_type_lkup, event_code_lkup, event_props = build_key_lookups(lines)
    data = []
    for line in lines:
        if re.match(VAL_LINE_PTRN, line):
            data.append(eval(re.sub(VAL_PTRN, r'\1', line))) # pylint: disable=W0123
    data = [[x[0] + (x[1] / 1000000),
            event_type_lkup[x[2]],
            event_code_lkup[x[3]],
            x[4]] for x in data]
    df = pd.DataFrame(data, columns=['time', 'type', 'code', 'val'])
    splits = {}
    for t in event_type_lkup.values():
        for c in event_code_lkup.values():
            k = df[df['type']==t]
            k = k[k['code']==c]
            if len(k) > 0:
                splits[c] = k
    return splits, event_type_lkup, event_code_lkup, event_props


def build_scatter_plot(splits):
    x_points = pd.DataFrame(splits['ABS_X']['val'])
    x_time = pd.DataFrame(splits['ABS_X']['time'])
    y_points = pd.DataFrame(splits['ABS_Y']['val'])
    y_time = pd.DataFrame(splits['ABS_Y']['time'])
    pressure_points = pd.DataFrame(splits['ABS_PRESSURE']['val'])
    pressure_time = pd.DataFrame(splits['ABS_PRESSURE']['time'])
    # Prepare a scatter plot of x=x-coord, y=y-coord, z=pressure
    xyp = pd.DataFrame()
    xyp_index = x_time.index.union(y_time.index).union(pressure_time.index)
    xyp = xyp.reindex(xyp_index, copy=False)
    xyp['X'] = x_points
    xyp['Y'] = y_points
    xyp['PRESSURE'] = pressure_points
    xyp['DPDT'] = np.gradient(xyp['PRESSURE'])
    xyp = xyp.interpolate(limit_direction='both')
    fig = plt.figure(figsize=(FIG_XY_DPI[0], FIG_XY_DPI[1]),
                     dpi=FIG_XY_DPI[2], tight_layout=False, constrained_layout=False)
    max_pressure = max(xyp['PRESSURE'])
    colors = [color(val[1]['PRESSURE'], val[1]['DPDT'], max_pressure) for val in xyp.iterrows()]
    scatter_axis = fig.add_axes(Axes3D(fig, azim=-35, elev=-145, auto_add_to_figure=False))
    scatter_axis.set_xbound(0, TRACKPAD_X_Y_PRESMAX[0])
    scatter_axis.set_ybound(0, TRACKPAD_X_Y_PRESMAX[1])
    scatter_axis.set_zbound(0, TRACKPAD_X_Y_PRESMAX[2])
    scatter = scatter_axis.scatter3D(xs=xyp['X'], ys=xyp['Y'], zs=xyp['PRESSURE'], c=colors)
    scatter.set_cmap('nipy_spectral_r')
    return plt


lines = read_file()
splits, event_type_lkup, event_code_lkup, event_props = parse_lines(lines)
plot = build_scatter_plot(splits)
plot.show()
