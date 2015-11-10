# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from contracts import contract
from contracts.utils import raise_desc, raise_wrapped
from mocdp.drawing import plot_upset_R2
from mocdp.posets.poset import NotLeq
from mocdp.posets.poset_product import PosetProduct
from mocdp.posets.rcomp import Rcomp
from mocdp.posets.types_universe import get_types_universe
from mocdp.posets.uppersets import UpperSet, UpperSets
import functools
import numpy as np

def generic_report(r, dp, trace, annotation=None, axis0=(0, 0, 0, 0)):
    plotters = {
        'UR2': PlotterUR2(),
        'URRpR_12': PlotterURRpR_12(),
        'URRpR_13': PlotterURRpR_13(),
        'URRpR_23': PlotterURRpR_23(),
    }
    R = dp.get_res_space()
    UR = UpperSets(R)

    with r.subsection('S', caption='S') as rr:
        space = trace.S
        sequence = trace.get_s_sequence()
        generic_try_plotters(rr, plotters, space, sequence, axis0=axis0,
                             annotation=annotation)

    with r.subsection('R', caption='R') as rr:
        space = UR
        sequence = trace.get_r_sequence()
        generic_try_plotters(rr, plotters, space, sequence, axis0=axis0,
                             annotation=annotation)


def generic_try_plotters(r, plotters, space, sequence, axis0=None, annotation=None):
    nplots = 0
    for name, plotter in plotters.items():
        try:
            plotter.check_plot_space(space)
        except NotPlottable:
            # print('Plotter %r cannot plot %r:\n%s' % (name, space, e))
            continue
        nplots += 1

        f = r.figure(name, cols=5)
        generic_plot_sequence(f, plotter, space, sequence, axis0=axis0, annotation=annotation)

    if not nplots:
        r.text('error', 'No plotters for %s' % space)


def join_axes(a, b):
    return (min(a[0], b[0]),
            max(a[1], b[1]),
            min(a[2], b[2]),
            max(a[3], b[3]))

def generic_plot_sequence(r, plotter, space, sequence, axis0=None, annotation=None):

    axis = plotter.axis_for_sequence(space, sequence)

    axis = enlarge(axis, 0.15)
    if axis0 is not None:
        axis = join_axes(axis, axis0)

    for i, x in enumerate(sequence):
        caption = space.format(x)
        caption = None
        with r.plot('S%d' % i, caption=caption) as pylab:
            plotter.plot(pylab, axis, space, x)
            if annotation is not None:
                annotation(pylab, axis)

            xlabel, ylabel = plotter.get_xylabels(space)
            if xlabel:
                pylab.xlabel(xlabel)
            if ylabel:
                pylab.ylabel(ylabel)

            if (axis[0] != axis[1]) or (axis[2] != axis[3]):
                pylab.axis(axis)

class NotPlottable(Exception):
    pass

class Plotter():
    __metaclass__ = ABCMeta

    @abstractmethod
    def check_plot_space(self, space):
        pass

    @abstractmethod
    @contract(returns='seq[4]')
    def axis_for_sequence(self, space, seq):
        pass

    @abstractmethod
    def plot(self, pylab, axis, space, value):
        pass

    def get_xylabels(self, _space):
        return None, None

class PlotterUR2(Plotter):

    def check_plot_space(self, space):
        tu = get_types_universe()
        if not isinstance(space, UpperSets):
            msg = 'I can only plot upper sets.'
            raise_desc(NotPlottable, msg, space=space)

        R2 = PosetProduct((Rcomp(), Rcomp()))
        P = space.P
        try:
            tu.check_leq(P, R2)
        except NotLeq as e:
            msg = ('cannot convert to R^2 from %s' % space)
            raise_wrapped(NotPlottable, e, msg)

        _f1, _f2 = tu.get_embedding(P, R2)

    def get_xylabels(self, space):
        P = space.P
        return '%s' % P[0], '%s' % P[1]

    @contract(returns='seq[4]')
    def axis_for_sequence(self, space, seq):
        self.check_plot_space(space)


        R2 = PosetProduct((Rcomp(), Rcomp()))
        tu = get_types_universe()
        P_TO_S, _ = tu.get_embedding(space.P, R2)

        points2d = [[(P_TO_S(_)) for _ in s.minimals] for s in seq]
        axes = [get_bounds(_) for _ in points2d]
        return enlarge(functools.reduce(reduce_bounds, axes), 0.1)

#
#
#         for s in seq:
#             points = map(P_TO_R2, s.minimals)
#         if len(points) == 0:
#             return (0, 1, 0, 1)
#         xs = [p[0] for p in points]
#         ys = [p[1] for p in points]
#         return (min(xs), max(xs), min(ys), max(ys))

    def plot(self, pylab, axis, space, value):
        self.check_plot_space(space)

        v = value
        plot_upset_R2(pylab, v, axis, color_shadow=[1.0, 0.8, 0.8])


# Upsets((R[s]×R[s])×R[s])
class PlotterURRpR(Plotter):
    def __init__(self):
        R = Rcomp()
        self.S = PosetProduct((PosetProduct((R, R)), R))

    @abstractmethod
    def toR2(self, z):
        pass

    def check_plot_space(self, space):
        tu = get_types_universe()
        if not isinstance(space, UpperSets):
            msg = 'I can only plot upper sets.'
            raise_desc(NotPlottable, msg, space=space)

        P = space.P
        try:
            tu.check_leq(P, self.S)
        except NotLeq as e:
            msg = ('cannot convert to %s from %s' % (P, self.S))
            raise_wrapped(NotPlottable, e, msg)

        _f1, _f2 = tu.get_embedding(P, self.S)

    @contract(returns='seq[4]')
    def axis_for_sequence(self, space, seq):
        self.check_plot_space(space)

        tu = get_types_universe()
        P_TO_S, _ = tu.get_embedding(space.P, self.S)

        points2d = [[self.toR2(P_TO_S(_)) for _ in s.minimals] for s in seq]
        axes = [get_bounds(_) for _ in points2d]
        return enlarge(functools.reduce(reduce_bounds, axes), 0.1)


    def plot(self, pylab, axis, space, value):
        self.check_plot_space(space)
        tu = get_types_universe()
        P_TO_S, _ = tu.get_embedding(space.P, self.S)

#         y =-x+sqrt(x)+10,
        # y>=-2x+ 2sqrt(x)+20.
        xs = np.linspace(0, 20, 100)
        ys = -2 * (xs - np.sqrt(xs) - 10)
        pylab.plot(xs, ys, '--')

        points2d = [self.toR2(P_TO_S(_)) for _ in value.minimals]

        R2 = PosetProduct((Rcomp(), Rcomp()))


        class MyUpperSet(UpperSet):

            def __init__(self, minimals, P):
                self.minimals = frozenset(minimals)
                self.P = P


        v = MyUpperSet(points2d, P=R2)
        plot_upset_R2(pylab, v, axis, color_shadow=[1.0, 0.8, 0.8])
        for p in points2d:
            pylab.plot(p[0], p[1], 'rx')

class PlotterURRpR_12(PlotterURRpR):

    def toR2(self, z):
        (a, b), _ = z
        return (a, b)

class PlotterURRpR_13(PlotterURRpR):

    def toR2(self, z):
        (a, _), c = z
        return (a, c)

class PlotterURRpR_23(PlotterURRpR):

    def toR2(self, z):
        (_, b), c = z
        return (b, c)



def enlarge(b, f):
    w = b[1] - b[0]
    h = b[3] - b[2]
    dw = f * w
    dh = h * f
    return (b[0] - dw, b[1] + dw, b[2] - dh, b[3] + dh)

def reduce_bounds(b1, b2):
    return (min(b1[0], b2[0]),
            max(b1[1], b2[1]),
            min(b1[2], b2[2]),
            max(b1[3], b2[3]))

def get_bounds(points):
    if not points:
        return (0, 0, 0, 0)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), max(xs), min(ys), max(ys))




