# -*- coding: utf-8 -*-
from .any import Any, BottomCompletion, TopCompletion
from .rcomp import Rcomp
from .space import Map
from contracts import contract
from contracts.utils import check_isinstance, raise_wrapped
from mocdp.exceptions import DPSyntaxError, mcdp_dev_warning
from pint import UnitRegistry  # @UnresolvedImport
from pint.unit import UndefinedUnitError  # @UnresolvedImport
import functools
import math



class MyUnitRegistry(UnitRegistry):
    def __init__(self, *args, **kwargs):
        UnitRegistry.__init__(self, *args, **kwargs)
        self.define(' dollars = [cost] = USD')
        self.define(' flops = [flops]')
        self.define(' pixels = [pixels]')
        self.define(' episodes = [episodes]')
        self.define(' CHF = 1.03 dollars')
        self.define(' EUR = 1.14 dollars')

_ureg = MyUnitRegistry()


def get_ureg():
    ureg = _ureg
    return ureg

class RcompUnits(Rcomp):

    def __init__(self, pint_unit):
        ureg = get_ureg()
        check_isinstance(pint_unit, ureg.Quantity)
            
        Rcomp.__init__(self)
        self.units = pint_unit

    def __repr__(self):
        # need to call it to make sure dollars i defined
        ureg = get_ureg()  # @UnusedVariable

        # graphviz does not support three-byte unicode
        # c = "ℝ̅"
        c = "ℝᶜ"

        if self.units == R_dimensionless.units:
            return '%s[]' % c

        return "%s[%s]" % (c, format_pint_unit_short(self.units))

    def __getstate__(self):
        # See: https://github.com/hgrecco/pint/issues/349
        u = self.units
        # This is a hack
        units_ex = (u.magnitude, u.units._units)
        # Original was:
        # units_ex = (u.magnitude, u.units)
        state = {'top': self.top, 'units_ex': units_ex}
        return state

    def __setstate__(self, x):
        self.top = x['top']
        units_ex = x['units_ex']
        ureg = get_ureg()
        self.units = ureg.Quantity(units_ex[0], units_ex[1])

    def __eq__(self, other):
        if isinstance(other, RcompUnits):
            eq = (other.units == self.units)
            return eq
        return False

    def format(self, x):
        if x == self.top:
            return self.top.__repr__()
        else:
            s = Rcomp.format(self, x)
            return '%s %s' % (s, format_pint_unit_short(self.units))


def parse_pint(s0):
    """ thin wrapper taking care of dollars not recognized """
    s = s0.replace('$', ' dollars ')
    ureg = get_ureg()
    try:
        return ureg.parse_expression(s)

    except (UndefinedUnitError, SyntaxError) as e:
        msg = 'Cannot parse units %r.' % s0
        raise_wrapped(DPSyntaxError, e, msg, compact=True)
        # ? for some reason compact does not have effect here
    except Exception as e:
        msg = 'Cannot parse units %r (%s).' % (s0, type(e))
        raise_wrapped(DPSyntaxError, e, msg)

def make_rcompunit(units):
    try:
        s = units.strip()
    
        mcdp_dev_warning('obsolete?')
        if s.startswith('set of'):
            t = s.split('set of')
            u = make_rcompunit(t[1])
            from mcdp_posets import FiniteCollectionsInclusion
            return FiniteCollectionsInclusion(u)

        if s == 'any':
            return BottomCompletion(TopCompletion(Any()))
    
        if s == 'R':
            s = 'm/m'
        unit = parse_pint(s)
    except DPSyntaxError as e:
        msg = 'Cannot parse %r.' % units
        raise_wrapped(DPSyntaxError, e, msg)
    return RcompUnits(unit)

def format_pint_unit_short(units):
    # some preferred ways
    if units == R_Power.units:  # units = A*V*s
        return 'W'
    if units == R_Energy.units:
        return 'J'
    if units == R_Weight.units:
        return 'kg'
    if units == R_Weight_g.units:
        return 'g'
    if units == R_Force.units:
        return 'N'

    x = '{:~}'.format(units)
    x = x.replace('1.0', '')
    if not '/' in x:
        x = x.replace('1', '')  # otherwise 1 / s -> / s
    x = x.replace('dollars', '$')
    x = x.replace(' ', '')
    x = x.replace('**', '^')
    x = x.replace('^2', '²')
    return str(x)

R_dimensionless = make_rcompunit('m/m')
R_Time = make_rcompunit('s')
R_Power = make_rcompunit('W')
R_Force = make_rcompunit('N')
R_Cost = make_rcompunit('$')
R_Energy = make_rcompunit('J')
R_Energy_J = make_rcompunit('J')
R_Weight = make_rcompunit('kg')
R_Weight_g = make_rcompunit('g')

R_Current = make_rcompunit('A')
R_Voltage = make_rcompunit('V')


def mult_table_seq(seq):
    return functools.reduce(mult_table, seq)

@contract(a=RcompUnits, b=RcompUnits)
def mult_table(a, b):
    unit2 = a.units * b.units
    return RcompUnits(unit2)

@contract(a=RcompUnits, num='int', den='int')
def rcompunits_pow(a, num, den):
    """
        Gets the unit for a ^ (num/den)
    """
    x = 1.0 * num / den
    u = a.units ** x
    return RcompUnits(u)

class RCompUnitsPower(Map):

    def __init__(self, F, num, den):
        R = rcompunits_pow(F, num, den)
        Map.__init__(self, dom=F, cod=R)
        self.num = num
        self.den = den

    def _call(self, x):
        if self.dom.equal(x, self.dom.get_top()):
            return self.cod.get_top()
        e = 1.0 * self.num / self.den
        try:
            r = math.pow(x, e)
            return r
        except OverflowError:
            return self.cod.get_top()

    def __repr__(self):
        s = '^ '
        s += '%d' % self.num
        if self.den != 1:
            s += '/%s' % self.den
        return s

        
