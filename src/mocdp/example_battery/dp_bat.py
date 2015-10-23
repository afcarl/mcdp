# -*- coding: utf-8 -*-
from contracts import contract
from mocdp.dp import PrimitiveDP
from mocdp.posets import PosetProduct, Rcomp
import numpy as np
from mocdp.posets import R_Energy, R_Weight, R_Time, R_Power
from mocdp.posets.space_product import SpaceProduct


class BatteryDP(PrimitiveDP):
    """ 
    
        F: need F Joule for energy
        R: need battery of weight W
        
    """
    @contract(energy_density='(int|float), >0')
    def __init__(self, energy_density):
        '''
        :param energy_density: Joule/gram
        '''
        self.energy_density = float(energy_density)

        M = SpaceProduct(())
        PrimitiveDP.__init__(self, F=R_Energy, R=R_Weight, M=M)
    
    def solve(self, min_func):
        funsp = self.get_fun_space()
        ressp = self.get_res_space()

        if min_func == funsp.get_top():
            return ressp.U(ressp.get_top())
        
        joules = min_func
        weight = joules / self.energy_density
        return ressp.U(weight)

#     def __repr__(self): return 'battery'

class Weight2totalpayload(PrimitiveDP):

    def __init__(self, baseline=100):
        self.baseline = baseline

        M = SpaceProduct(())
        R = Rcomp()
        F = Rcomp()
        PrimitiveDP.__init__(self, F=F, R=R, M=M)

    def solve(self, min_func):
        funsp = self.get_fun_space()
        ressp = self.get_res_space()
        funsp.belongs(min_func)

        if min_func == funsp.get_top():
            return ressp.U(ressp.get_top())

        battery_weight = min_func
        payload = self.baseline + battery_weight

        return ressp.U(payload)


class Payload2energy(PrimitiveDP):

    def __init__(self, T, alpha):
        self.T = T
        self.alpha = alpha

        M = SpaceProduct(())
        PrimitiveDP.__init__(self, F=Rcomp(), R=Rcomp(), M=M)

    def solve(self, min_func):
        funsp = self.get_fun_space()
        ressp = self.get_res_space()
        funsp.belongs(min_func)

        if min_func == funsp.get_top():
            return ressp.U(ressp.get_top())

        payload = min_func
        energy = payload * self.alpha * self.T
        return ressp.U(energy)


def T(Ps):
    if Ps == 0:
        return R_Time.get_top()
        # raise ValueError(Ps)
    return 10.0 + 1.0 / np.sqrt(Ps)

def Pa_from_weight(W):
    return 1.0 + W

class Payload2ET(PrimitiveDP):
    """ Example 16 in RAFC """
    def __init__(self):
        F = Rcomp()
        M = R_Power
        R = PosetProduct((Rcomp(), Rcomp()))
        PrimitiveDP.__init__(self, F=F, R=R, M=M)

    def evaluate_f_m(self, func, m):
        self.F.belongs(func)
        self.M.belongs(m)
        W = func
        Ps = m
        return self._r_from_W_Ps(W, Ps)

    def _r_from_W_Ps(self, W, Ps):
        if Ps == 0:
            return (0.0, R_Time.get_top())
        P2E = lambda Ps: T(Ps) * (Pa_from_weight(W) + Ps)
        return (P2E(Ps), T(Ps))

    def solve(self, min_func):
        funsp = self.get_fun_space()
        ressp = self.get_res_space()

        if min_func == funsp.get_top():
            return ressp.U(ressp.get_top())

        W = min_func

#         PS = np.logspace(1e-5, 1e5, 20)
        # paper PS = np.linspace(0.01, 5.0, 500)
        PS = np.linspace(0.01, 5.0, 10)

        choices = [ self._r_from_W_Ps(W, Ps) for Ps in PS ]

        for c in choices:
            ressp.belongs(c)

        from mocdp.posets.utils import poset_minima
        min_choices = poset_minima(choices, ressp.leq)

        # print('Choices: %d down to %d' % (len(choices), len(min_choices)))
        return ressp.Us(min_choices)
#     def __repr__(self):
#         return 'Payload2ET(%s,%s)' % (self.F, self.R)

class ET2Payload(PrimitiveDP):
    """ Example 16 in RAFC """
    def __init__(self, Tmax, W0, rho):
        self.Tmax = Tmax
        self.W0 = W0
        self.rho = rho

        F = PosetProduct((R_Energy, R_Time))
        R = R_Weight
        M = SpaceProduct(())
        PrimitiveDP.__init__(self, F=F, R=R, M=M)
#
#     def __repr__(self):
#         return 'ET2Payload(Tmax=%.2f;W0=%.2f;rho=%.2f)' % (self.Tmax, self.W0, self.rho)


    def solve(self, min_func):
        funsp = self.get_fun_space()
        ressp = self.get_res_space()
        funsp.belongs(min_func)

        if min_func == funsp.get_top():
            return ressp.U(ressp.get_top())

        (E, T) = min_func
        
        if T > self.Tmax:
            return ressp.U(ressp.get_top())

        W = self.W0 + (1.0 / self.rho) * E

        return ressp.U(W)
"""
dp BatteryDP:
    energy_density = 12 
    icon battery
    
    F stored_energy (J)
    R battery_weight (g)
    
    battery_weight ≥ stored_energy * $energy_density
    
weight2payload = 
dp:
    "This is a simple"
    
    desc:
        This is a simple relation between payload and 
        weight:
        
        $ P ≥ X * x $
    
    C:
        baseline (g) = 100.0  "Baseline payload" 
        
    F:
        battery_weight (g)   "Weight of battery to carry"
          
    R:
        total_payload  (g)  "Payload"  $P$ 
    
    total_payload ≥ battery_weight + baseline
    
dp payload2energy:
    
    F payload (g) "Carry the payload @." tex P
    R energy  (J) "Required stored energy @." tex E

dp rafc_example:

    dp energy2bweight = BatteryDP()
    dp weight2payload = weight2payload() 
    dp payload2energy = payload2energy / {battery: 0.1, battery.pok: 0.1}   

    energy2bweight |-- energy ≤ required --| weight2payload   

    dp 0 = MCB_plus_PSU
    dp 1 = chassis_plus_motor

    F velocity = velocity─┤1
    F extra_payload (g)   "Extra payload"
    F extra_power   (P)   "Extra power"
    F mission_time = mission_time─┤0

    please hurry !!!!111 
    
""" 
