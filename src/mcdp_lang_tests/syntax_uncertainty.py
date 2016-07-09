from comptests.registrar import comptest
from mcdp_dp.dp_transformations import get_dp_bounds
from mcdp_lang import parse_ndp
from mcdp_posets import UpperSet, UpperSets
from mcdp_dp.primitive import WrongUseOfUncertain
from contracts.utils import raise_desc

@comptest
def check_uncertainty1():
    ndp = parse_ndp("""
        mcdp {
            requires r1 [USD]
            r1 >= Uncertain(1 USD, 2USD)
        }
    """)
    dp = ndp.get_dp()
    dpl, dpu = get_dp_bounds(dp, 1, 1)
    UR = UpperSets(dp.get_res_space())
    f = ()
    sl = dpl.solve(f)
    su = dpu.solve(f)
    UR.check_leq(sl, su)

@comptest
def check_uncertainty2():
    ndp = parse_ndp("""
        mcdp {
            provides f1 [N]
            f1 <= Uncertain(1 N, 2 N)
        }
    """)
    
    dp = ndp.get_dp()
    dpl, dpu = get_dp_bounds(dp, 1, 1)

    R = dp.get_res_space()
    UR = UpperSets(R)
    f0 = 0.0  # N
    sl = dpl.solve(f0)
    su = dpu.solve(f0)
    UR.check_leq(sl, su)
    print sl
    print su

    f0 = 1.5  # N
    sl = dpl.solve(f0)
    su = dpu.solve(f0)
    UR.check_leq(sl, su)
    print sl
    print su
    feasible = UpperSet(set([()]), R)
    infeasible = UpperSet(set([]), R)
    sl_expected = feasible
    su_expected = infeasible
    print sl_expected
    print su_expected
    UR.check_equal(sl, sl_expected)
    UR.check_equal(su, su_expected)



@comptest
def check_uncertainty4():
    """ This will give an error somewhere """
    ndp = parse_ndp("""
mcdp {
    requires r1 [USD]
    r1 >= Uncertain(2 USD, 1 USD)
}

"""
 )
    # > DPSemanticError: Run-time check failed; wrong use of "Uncertain" operator.
    # > l: Instance of <type 'float'>.
    # >    2.0
    # > u: Instance of <type 'float'>.
    # >    1.0
    dp = ndp.get_dp()
    dpl, dpu = get_dp_bounds(dp, 1, 1)

    f = ()
    try:
        dpl.solve(f)
    except WrongUseOfUncertain as e:
        pass
    else:
        msg = 'Expected WrongUseOfUncertain.'
        raise_desc(Exception, msg)

    try:
        dpu.solve(f)
    except WrongUseOfUncertain as e:
        pass
    else:
        msg = 'Expected WrongUseOfUncertain.'
        raise_desc(Exception, msg)


@comptest
def check_uncertainty3():

    s = """
mcdp {
  provides capacity [J]
  requires mass     [kg]

  required mass * Uncertain(2 J/kg, 3 J/kg) >= provided capacity
}
"""
    ndp = parse_ndp(s)
    dp = ndp.get_dp()
    R = dp.get_res_space()
    UR = UpperSets(R)
    dpl, dpu = get_dp_bounds(dp, 100, 100)
    f0 = 1.0  # J
    sl = dpl.solve(f0)
    su = dpu.solve(f0)
    print sl
    print su
    UR.check_leq(sl, su)

    real_lb = UpperSet(set([0.333333]), R)
    real_ub = UpperSet(set([0.500000]), R)

    # now dpl will provide a lower bound from below
    UR.check_leq(sl, real_lb)
    # and dpu will provide the upper bound from above
    UR.check_leq(real_ub, su)


@comptest
def check_uncertainty5():

    s = """
mcdp {
  provides capacity [Wh]
  requires mass     [kg]

  required mass * Uncertain(100 Wh/kg, 120 Wh/kg) >= provided capacity

}"""
    ndp = parse_ndp(s)
    dp = ndp.get_dp()
    R = dp.get_res_space()
    UR = UpperSets(R)
    dpl, dpu = get_dp_bounds(dp, 1000, 1000)
    f0 = 1.0  # J
    sl = dpl.solve(f0)
    su = dpu.solve(f0)
    UR.check_leq(sl, su)
    print sl
    print su


@comptest
def check_uncertainty6():
    pass
#     s = """
# mcdp {
#   provides capacity [J]
#   requires mass     [kg]
#
#   required mass * Uncertain(100 J/kg, 120 J/kg) >= provided capacity
#
# }"""
#     ndp = parse_ndp(s)
#     dp = ndp.get_dp()
#     dpl, dpu = get_dp_bounds(dp, 100, 100)
#     f0 = 1.0  # J
#     sl = dpl.solve(f0)
#     su = dpu.solve(f0)
#     print sl
#     print su

