# -*- coding: utf-8 -*-
from contracts import contract
from contracts.utils import raise_desc
from mcdp_dp import Identity, get_approx_dp
from mcdp_posets import Space
from mocdp.comp.composite import CompositeNamedDP
from mocdp.comp.context import (Connection, get_name_for_fun_node,
    get_name_for_res_node)
from mocdp.comp.interfaces import NamedDP
from mocdp.comp.wrap import dpwrap


__all__ = ['make_approximation']

@contract(name=str,
          approx_perc='float|int',
          approx_abs='float|int', approx_abs_S=Space, ndp=NamedDP,
          returns=NamedDP)
def make_approximation(name, approx_perc, approx_abs, approx_abs_S, max_value, max_value_S, ndp):
    fnames = ndp.get_fnames()
    rnames = ndp.get_rnames()

    if name in fnames:
        return make_approximation_f(name, approx_perc, approx_abs, approx_abs_S,
                                    max_value, max_value_S, ndp)

    if name in rnames:
        return make_approximation_r(name, approx_perc, approx_abs, approx_abs_S,
                                    max_value, max_value_S, ndp)

    msg = 'Could not find name in either functions or resources.'
    raise_desc(ValueError, msg, fnames=fnames, rnames=rnames, name=name)


NAME_ORIGINAL = '_original'
NAME_APPROX = '_approx'

def make_approximation_r(name, approx_perc, approx_abs, approx_abs_S,
                         max_value, max_value_S, ndp):
    R = ndp.get_rtype(name)
    ndp_after = get_approx_dp(R, name, approx_perc, approx_abs, approx_abs_S, max_value, max_value_S)

    name2ndp = {NAME_ORIGINAL: ndp, NAME_APPROX: ndp_after}
    fnames = ndp.get_fnames()
    rnames = ndp.get_rnames()

    connections = []
    connections.append(Connection(NAME_ORIGINAL, name, NAME_APPROX, name))

    for fn in fnames:
        F = ndp.get_ftype(fn)
        fn_ndp = dpwrap(Identity(F), fn, fn)
        fn_name = get_name_for_fun_node(fn)
        name2ndp[fn_name] = fn_ndp
        connections.append(Connection(fn_name, fn, NAME_ORIGINAL, fn))

    for rn in rnames:
        R = ndp.get_rtype(rn)
        rn_ndp = dpwrap(Identity(R), rn, rn)
        rn_name = get_name_for_res_node(rn)
        name2ndp[rn_name] = rn_ndp
        if rn == name:
            connections.append(Connection(NAME_APPROX, rn, rn_name, rn))
        else:
            connections.append(Connection(NAME_ORIGINAL, rn, rn_name, rn))

    return CompositeNamedDP.from_parts(name2ndp, connections, fnames, rnames)

def make_approximation_f(name, approx_perc, approx_abs, approx_abs_S,
                         max_value, max_value_S, ndp):
    F = ndp.get_ftype(name)
    ndp_before = get_approx_dp(F, name, approx_perc, approx_abs, approx_abs_S, max_value, max_value_S)

    name2ndp = {NAME_ORIGINAL: ndp, NAME_APPROX: ndp_before}
    fnames = ndp.get_fnames()
    rnames = ndp.get_rnames()

    connections = []
    connections.append(Connection(NAME_APPROX, name, NAME_ORIGINAL, name))

    for fn in fnames:
        F = ndp.get_ftype(fn)
        fn_ndp = dpwrap(Identity(F), fn, fn)
        fn_name = get_name_for_fun_node(fn)
        name2ndp[fn_name] = fn_ndp
        if fn == name:
            connections.append(Connection(fn_name, fn, NAME_APPROX, fn))
        else:
            connections.append(Connection(fn_name, fn, NAME_ORIGINAL, fn))

    for rn in rnames:
        R = ndp.get_rtype(rn)
        rn_ndp = dpwrap(Identity(R), rn, rn)
        rn_name = get_name_for_res_node(rn)
        name2ndp[rn_name] = rn_ndp
        connections.append(Connection(NAME_ORIGINAL, rn, rn_name, rn))

    return CompositeNamedDP.from_parts(name2ndp, connections, fnames, rnames)
