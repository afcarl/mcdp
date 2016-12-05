# -*- coding: utf-8 -*-
from nose.tools import assert_raises

from comptests.registrar import comptest, run_module_tests
from mcdp_dp import JoinNDP, MeetNDP
from mcdp_dp.dp_dummy import Template
from mcdp_dp.dp_inv_mult import InvMult2Nat
from mcdp_dp.dp_inv_plus import InvPlus2, InvPlus2Nat
from mcdp_dp.dp_series import Series
from mcdp_dp.primitive import NotSolvableNeedsApprox
from mcdp_lang.parse_interface import parse_poset, parse_template, parse_ndp
from mcdp_maps import ProductNNatMap
from mcdp_posets import Nat
from mcdp_posets_tests.utils import assert_belongs, assert_does_not_belong
from mocdp import MCDPConstants
from mocdp.comp.composite_makecanonical import connect_resources_to_outside, \
    connect_functions_to_outside
from mocdp.comp.wrap import dpwrap
from mocdp.exceptions import DPInternalError, DPSemanticError


@comptest
def check_product1():
    
    amap = ProductNNatMap(4)

    assert amap((1,3,4,5)) == 5*4*3
    
    # TODO: make separate tests
    
@comptest
def check_join_meet_1():
    # test meet 
    # ⟨f₁, f₂⟩ ⟼ { min(f₁, f₂) }
    # r ⟼  { ⟨r, ⊤⟩, ⟨⊤, r⟩ }
    
    N = Nat()
    dp = MeetNDP(2, N)
    lf = dp.solve_r(5)
    #print('lf: {}'.format(lf))
    assert_belongs(lf, (10, 5))
    assert_belongs(lf, (5, 10))
    assert_does_not_belong(lf, (10, 10))
    
    Rtop = N.get_top()
    lf2 = dp.solve_r(Rtop)
    #print('lf2: {}'.format(lf2))
    assert_belongs(lf2, (10, 10))
    assert_belongs(lf2, (Rtop, Rtop))
    
    lf3 = dp.solve_r(0)
    #print('lf3: {}'.format(lf3))
    assert_belongs(lf3, (0, 0))
    assert_does_not_belong(lf3, (0, 1))
    assert_does_not_belong(lf3, (1, 0))
    
    
    #    Join ("max") of n variables. 
    #    ⟨f₁, …, fₙ⟩ ⟼ { max(f₁, …, fₙ⟩ }
    #    r ⟼ ⟨r, …, r⟩
    dp = JoinNDP(3, N)
    ur = dp.solve((10, 3, 3))
    assert_belongs(ur, 10)
    assert_does_not_belong(ur, 9)
    
    lf = dp.solve_r(10)
    assert_does_not_belong(lf, (0, 11, 0))
    assert_belongs(lf, (0, 10, 0))
    assert_belongs(lf, (0, 9, 0))
    
    
@comptest
def test_series_invalid():
    """ invalid argument for Series """
    F1 = parse_poset('s')
    R1 = parse_poset('s')
    F2 = parse_poset('m')
    R2 = parse_poset('g')
    dp1 = Template(F1, R1)
    dp2 = Template(F2, R2)
    assert_raises(DPInternalError, Series, dp1,dp2)
    
@comptest
def test_exc_connect_resources_to_outside():
    F1 = parse_poset('s')
    R1 = parse_poset('s')
    dp = Template(F1, R1)
    ndp = dpwrap(dp, 'f1', 'r1')
    ndp_name = 'name'
    name2ndp = {ndp_name: ndp}
    connections = []
    rnames = ['r1', 'notpresent']
    
    assert_raises(ValueError, 
                  connect_resources_to_outside, name2ndp, connections, ndp_name, rnames)
    
@comptest
def test_exc_connect_functions_to_outside():
    F1 = parse_poset('s')
    R1 = parse_poset('s')
    dp = Template(F1, R1)
    ndp = dpwrap(dp, 'f1', 'r1')
    ndp_name = 'name'
    name2ndp = {ndp_name: ndp}
    connections = []
    fnames = ['f1', 'notpresent']
    
    assert_raises(ValueError, 
                  connect_functions_to_outside, name2ndp, connections, ndp_name, fnames)
    

#     def connect_resources_to_outside(name2ndp, connections, ndp_name, rnames): 
#     """  
#         For each function in fnames of ndp_name, 
#         create a new outside function node and connect it to ndp_name. 
#     """ 
#     assert ndp_name in name2ndp 
#     ndp = name2ndp[ndp_name] 
#  
#     if not set(rnames).issubset(ndp.get_rnames()): 
#         msg = 'Some of the resources are not present.' 
#         raise_desc(ValueError, msg, rnames=rnames, ndp=ndp) 

@comptest
def test_exc_InvPlus2():
    F = parse_poset('g')
    Rs = (parse_poset('g'),parse_poset('kg'))
    assert_raises(DPInternalError, InvPlus2, F, Rs)

    F = parse_poset('kg')
    Rs = (parse_poset('g'),parse_poset('g'))
    assert_raises(DPInternalError, InvPlus2, F, Rs)
    
    
@comptest
def test_antichain_size():
    
    M = MCDPConstants.InvPlus2Nat_max_antichain_size + 1
    F = Nat()
    Rs = (F, F)
    dp = InvPlus2Nat(F, Rs)
    
    assert_raises(NotSolvableNeedsApprox, dp.solve, M)
    
@comptest
def test_ex_InvMult2Nat():
    F = Nat()
    Rs = (F, F, F) # too many!
    
    assert_raises(ValueError, InvMult2Nat, F, Rs)
    

@comptest
def test_ex_invmult_limit():
    f = MCDPConstants.InvPlus2Nat_max_antichain_size + 1
    F = Nat()
    Rs = (F, F)
    dp = InvMult2Nat(F, Rs)
    assert_raises(NotSolvableNeedsApprox, dp.solve, f)
 
@comptest
def template_repeated_params():
    s = """
    template [A: `unused, A: `unused] mcdp { } 
    """
    assert_raises(DPSemanticError, parse_template, s)

@comptest
def unknown_operation_res():
    s = """
    mcdp { 
        provides f [m]
        requires x = not_existing(provided f)
    } 
    """
    # DPSemanticError: Unknown operation 'not_existing'.
    assert_raises(DPSemanticError, parse_ndp, s)


@comptest
def unknown_operation_fun():
    s = """
    mcdp { 
        requires r [m]
        provides f = not_existing(required r)
    } 
    """
    # DPSemanticError: Unknown operation 'not_existing'.
    assert_raises(DPSemanticError, parse_ndp, s)
    
@comptest
def addbottom():
    s = """
    add_bottom g
    """
    assert_raises(DPSemanticError, parse_poset, s)
    # DPSemanticError: You can use add_bottom only on a FinitePoset
    
    
# @comptest
# def product():
#     s = """
#     mcdp {
#         provides f1, f2 [g]
#         requires r = provided f1 * provided f2
#     }
#     """
#     ndp = parse_ndp(s)
#     
#     dp = ndp.get_dp()
#     dpL, dpU = get_dp_bounds(dp, nl=10, nu=10)
#     print dp.repr_long()
#     print dpL.repr_long()
#     print dpU.repr_long()
    # DPSemanticError: You can use add_bottom only on a FinitePoset
    
@comptest
def check_repeated_poset():
    s = """ poset {
        a 
        a <= b
        }
    """
    parse_poset(s)
    
    s = """ poset{
        a 
        a 
        }
    """
    
    # mocdp.exceptions.DPSemanticError: Repeated element 'a'.
    assert_raises(DPSemanticError, parse_poset, s)
    
    
if __name__ == '__main__': 
    
    run_module_tests()
    
    
    
    