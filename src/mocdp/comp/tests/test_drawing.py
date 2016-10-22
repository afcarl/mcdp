# -*- coding: utf-8 -*-
import os

from matplotlib.font_manager import FontProperties

from mcdp_dp import NotSolvableNeedsApprox
from mcdp_dp.dp_transformations import get_dp_bounds
from mcdp_posets import Rcomp
from mcdp_report.report import report_dp1
from mcdp_tests.generation import for_all_nameddps_dyn
from mocdp.comp.interfaces import NotConnected
from mocdp.exceptions import mcdp_dev_warning
from reprep import Report


@for_all_nameddps_dyn
def nameddp1_report(context, _id_dp, ndp):
    try:
        ndp.check_fully_connected()
    except NotConnected:
        print('Skipping because not connected.')
        return
    
    dp = ndp.get_dp()
    r = context.comp(report_dp1, dp)
    context.add_report(r, 'nameddp1')

mcdp_dev_warning('disabled this for now')
#@for_all_nameddps_dyn
def nameddp1_solve(context, _id_ndp, ndp):
    try:
        ndp.check_fully_connected()
    except NotConnected:
        print('Skipping because not connected.')
        return
    
    dp = ndp.get_dp()
    funsp = dp.get_fun_space()
    ressp = dp.get_res_space()

    if not is_scalar(funsp) or not is_scalar(ressp):
        return

    solutions = context.comp(solve_ndp, ndp, n=30)
    r = context.comp(report_solutions, ndp, solutions)
    context.add_report(r, 'report_solutions')

def unzip(iterable):
    return zip(*iterable)

def report_solutions(ndp, solutions):
    r = Report()
    return r

#     
#     
#     fnames = ndp.get_fnames()
#     rnames = ndp.get_rnames()
#     assert len(fnames) == 1
#     assert len(rnames) == 1
#     xl = '%s (%s)' % (fnames[0], ndp.get_ftype(fnames[0]))
#     yl = '%s (%s)' % (rnames[0], ndp.get_rtype(rnames[0]))
# 
# 
#     f, rmin = unzip(solutions)
#     
#     with r.plot() as pylab:
#         def gety(x):
#             return list(x.minimals)[0]
#         
#         y = map(gety, rmin)
#         print f
#         print y
# 
#         def is_finite(r):
#             return isinstance(r, float)
# 
#         def get_finite_part(a, b):
#             return unzip([(f, r) for (f, r) in zip(a, b)
#                           if is_finite(r)
#                           and is_finite(f)])
# 
#         def get_unfeasible_f(a, b):
#             return [f for (f, r) in zip(a, b) if not is_finite(r) and
#                     is_finite(f)  # no top
#                     ]
# 
#         f0, y0 = get_finite_part(f, y)
#         print f0, y0
#         fu = get_unfeasible_f(f, y)
# 
#         pylab.plot(f0, y0, 'k.')
#         pylab.plot(fu, 0 * np.array(fu), 'rs')
#         pylab_xlabel_unicode(pylab, xl)
#         pylab_ylabel_unicode(pylab, yl)
# 
#     return r


def pylab_label_generic(pf, s):
    prop = FontProperties()
#     f = '/Volumes/1506-env_fault/sw/canopy/User/lib/python2.7/site-packages/matplotlib/mpl-data/fonts/ttf/STIXGeneral.ttf'
    fs = ['/Library/Fonts/Microsoft/Cambria Math.ttf']
    for f in fs:
        if os.path.exists(f):
            prop.set_file(f)
            break
    sd = s.decode('utf-8')
    pf(sd, fontproperties=prop)

def pylab_xlabel_unicode(pylab, xl):
    pylab_label_generic(pylab.xlabel, xl)


def pylab_ylabel_unicode(pylab, yl):
    pylab_label_generic(pylab.ylabel, yl)
#
#     try:
#         pylab.ylabel(yl)
#     except UnicodeDecodeError as e:
#         yl = yl.decode('utf-8')
#         pylab.ylabel(yl)
#         # print('Cannot set label %s %r: %s' % (yl, yl, e))


def solve_ndp(ndp, n=20):
    
    dp = ndp.get_dp()
    funsp = dp.get_fun_space()
    chain = funsp.get_test_chain(n=n)
    try:
        results = map(dp.solve, chain)
    except NotSolvableNeedsApprox:
        nl = 10
        nu = 10
        dpL, dpU = get_dp_bounds(dp, nl, nu)
        results = map(dpL.solve, chain)
        
    return zip(chain, results)

        
def is_scalar(space):
    return isinstance(space, Rcomp)
