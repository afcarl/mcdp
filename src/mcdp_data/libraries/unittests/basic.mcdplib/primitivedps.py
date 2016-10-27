# -*- coding: utf-8 -*-
from mcdp_dp import (CatalogueDP, CoProductDP, CoProductDPLabels, Constant,
    ConstantMinimals, DPLoop0, DPLoop2, Identity, InvMult2, InvMult2L, InvMult2U,
    InvPlus2, InvPlus2L, InvPlus2Nat, InvPlus2U, JoinNDP, Limit, LimitMaximals,
    Max1, MeetNDualDP,  Mux, Parallel, ParallelN, Series0, Terminator,
    UncertainGate, UncertainGateSym, MeetNDP, JoinNDualDP)
from mcdp_lang import parse_poset
from mcdp_posets import FiniteCollectionAsSpace, PosetProduct
from mcdp_dp.dp_dummy import Template

def PlusValueDP1():
    from mcdp_dp import PlusValueDP
    F = parse_poset('J')
    U = parse_poset('mJ')
    v = 1000.0
    return PlusValueDP(F, c_value=v, c_space=U)

def PlusValueRcompDP():
    from mcdp_dp import PlusValueRcompDP
    return PlusValueRcompDP(2.1)

def PlusValueNatDP():
    from mcdp_dp import PlusValueNatDP
    return PlusValueNatDP(2)


def CatalogueDP1():
    m1 = 'A'
    m2 = 'B'
    m3 = 'C'
    M = FiniteCollectionAsSpace([m1, m2, m3])
    F = parse_poset('V')
    R = parse_poset('J')
    
    entries = [
        (m1, 1.0, 2.0),
        (m2, 2.0, 4.0),
        (m3, 3.0, 6.0),
    ]
    return CatalogueDP(F, R, M, entries)

def Constant1():
    R = parse_poset('V')
    value = 1.0
    return Constant(R, value)

def ConstantMinimals1():
    R = parse_poset('V x V')
    values = [(1.0, 0.0), (0.5, 0.5)]
    return ConstantMinimals(R, values)

def CoProductDP1():
    dps = (CatalogueDP1(), CatalogueDP1())
    return CoProductDP(dps)

def UncertainGate1():
    F = parse_poset('Nat')
    return UncertainGate(F)

def CoProductDPLabels1():
    dp = CoProductDP1()
    labels = ['label1', 'label2']
    return CoProductDPLabels(dp, labels)

def Mux1():
    """ a -> a """
    F = parse_poset('Nat')
    coords = ()
    return Mux(F, coords)

def Mux2():
    """ <a> -> a """
    P0 = parse_poset('Nat')
    F = PosetProduct((P0,))
    coords = 0
    return Mux(F, coords)

def Mux3():
    """ a -> <a> """
    F = parse_poset('Nat')
    coords = [()]
    return Mux(F, coords)

def Mux4():
    """ <a, <b, c> > -> < <a, b>, c> """
    F = parse_poset('J x (m x Hz)')
    coords = [ [0, (1, 0)], (1,1)]
    return Mux(F, coords)

def Mux5():
    """  One with a 1:

        <a, *> -> a
    """
    N = parse_poset('Nat')
    One = PosetProduct(())
    P = PosetProduct((N, One))
    coords = 0
    return Mux(F, coords)

 
def Identity1():
    F = parse_poset('V')
    return Identity(F)

def InvMult21():
    F = parse_poset('m')
    R1 = parse_poset('s')
    R2 = parse_poset('m/s')
    R = (R1, R2)
    return InvMult2(F, R)

def InvMult2U1():
    F = parse_poset('m')
    R1 = parse_poset('s')
    R2 = parse_poset('m/s')
    R = (R1, R2)
    n = 8
    return InvMult2U(F, R, n)

def InvMult2L1():
    F = parse_poset('m')
    R1 = parse_poset('s')
    R2 = parse_poset('m/s')
    R = (R1, R2)
    n = 8
    return InvMult2L(F, R, n)

def InvPlus2Nat1():
    F = parse_poset('Nat')
    Rs = (F, F)
    return InvPlus2Nat(F, Rs)

def InvPlus2_1():
    F = parse_poset('m')
    Rs = (F, F)
    return InvPlus2(F, Rs)

def InvPlus2U_1():
    F = parse_poset('m')
    Rs = (F, F)
    n = 9
    return InvPlus2U(F, Rs, n)

def InvPlus2L_1():
    F = parse_poset('m')
    Rs = (F, F)
    n = 9
    return InvPlus2L(F, Rs, n)

def Limit_1():
    F = parse_poset('m')
    value = 5.0
    return Limit(F, value)

def LimitMaximals_1():
    F = parse_poset('Nat x Nat')
    values = [(5, 1), (1, 5)]
    return LimitMaximals(F, values)

def Max1_1():
    F = parse_poset('Nat')
    f = 4
    return Max1(F, f)

 
def Template_1():
    P = parse_poset('m')
    F = P
    R = PosetProduct((P,P))
    return Template(F, R)



def DPLoop0_1():
    F1 = parse_poset('N')
    F2 = parse_poset('m')
    R = F2
    F = PosetProduct((F1, F2))
    dp = Template(F, R)
    return DPLoop0(dp)

def DPLoop2_1():
    F1 = parse_poset('N')
    R1 = parse_poset('J')
    F2 = parse_poset('m')
    R2 = F2
    F = PosetProduct((F1, F2))
    R = PosetProduct((R1, R2))
    dp = Template(F, R)
    return DPLoop2(dp)

def Parallel_1():
    dp1 = CatalogueDP1()
    dp2 = CatalogueDP1()
    return Parallel(dp1, dp2)

def ParallelN_1():
    dps = (CatalogueDP1(), CatalogueDP1(),  CatalogueDP1())
    return ParallelN(dps)

def Series0_1():
    dp1 = Constant1() # R = V
    V = parse_poset('V')
    dp2 = Max1(V, 2.0)
    return Series0(dp1, dp2)

def Terminator_1():
    F = parse_poset('Nat')
    return Terminator(F)

def UncertainGate_1():
    F0 = parse_poset('Nat')
    return UncertainGate(F0)

def UncertainGateSym_1():
    F0 = parse_poset('Nat')
    return UncertainGateSym(F0)

def JoinNDualDP_1():
    n = 3
    F0 = parse_poset('Nat')
    return JoinNDualDP(n, F0)

def JoinNDP_1():
    n = 3
    F = parse_poset('Nat')
    return JoinNDP(n, F)

def MeetNDualDP_1():
    n = 3
    P = parse_poset('Nat')
    return MeetNDualDP(n, P)
 
def MeetNDP_1():
    n = 3
    P = parse_poset('Nat')
    return MeetNDP(n, P)
    

