# -*- coding: utf-8 -*-
from .rcomp import Rcomp
from pint import UnitRegistry
import functools
from contracts.utils import check_isinstance, raise_wrapped
from mocdp.exceptions import DPSyntaxError

# __all__ = [
#    'RcompUnits',
#    'ureg',
#    'make_rcompunit',
#     'mult_table',
#     'mult_table_seq',
# ]

class MyUnitRegistry(UnitRegistry):
    def __init__(self, *args, **kwargs):
        UnitRegistry.__init__(self, *args, **kwargs)
        self.define(' dollars = [cost]')
_ureg = MyUnitRegistry()


def get_ureg():
    ureg = _ureg
    return ureg

class RcompUnits(Rcomp):

#     @contract(pint_unit=ureg.Quantity)
    def __init__(self, pint_unit, extra):
        ureg = get_ureg()
        check_isinstance(pint_unit, ureg.Quantity)
            
        Rcomp.__init__(self)
        self.units = pint_unit

    def __repr__(self):
        # need to call it to make sure dollars i defined
        ureg = get_ureg()  # @UnusedVariable


        s = Rcomp.__repr__(self)
        if self == R_dimensionless:
            return s
        return s + "[%s]" % format_pint_unit_short(self.units)

    def __getstate__(self):
        u = self.units
        units_ex = (u.magnitude, u.units)
        return {'top': self.top, 'units_ex': units_ex}

    def __setstate__(self, x):
        self.top = x['top']
        units_ex = x['units_ex']
        ureg = get_ureg()
        self.units = ureg.Quantity(units_ex[0], units_ex[1])

    def __eq__(self, other):
        if not isinstance(other, Rcomp):
            return False

        # need to call it to make sure dollars i defined
        ureg = get_ureg()  # @UnusedVariable

        if isinstance(other, RcompUnits):
#             print('comparing %s and %s' % (str((self.units).__repr__()),
#                                            str(other.units.__repr__())))
            return other.units.dimensionality == self.units.dimensionality

        return True

def parse_pint(s):
    """ thin wrapper taking care of dollars not recognized """
    s = s.replace('$', ' dollars ')
    ureg = get_ureg()
    try:
        return ureg.parse_expression(s)
    except Exception as e:
        msg = 'Cannot parse units.'
        raise_wrapped(DPSyntaxError, e, msg, s=s)

def make_rcompunit(units):
    s = units.strip()
    if s == 'R':
        s = 'm/m'
    unit = parse_pint(s)
    return RcompUnits(unit, extra=None)

def format_pint_unit_short(units):
    # some preferred ways
    if units == R_Power.units:  # units = A*V*s
        return 'W'
    if units == R_Energy.units:
        return 'J'
    if units == R_Force.units:
        return 'N'

    x = '{:~}'.format(units)
    x = x.replace('1.0', '')
    x = x.replace('1', '')
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
R_Weight = make_rcompunit('g')
R_Current = make_rcompunit('A')
R_Voltage = make_rcompunit('V')


def mult_table_seq(seq):
    return functools.reduce(mult_table, seq)

def mult_table(a, b):
    unit2 = a.units * b.units
    return RcompUnits(unit2, extra=None)
#
#     if a == R_dimensionless:
#         return b
#     if b == R_dimensionless:
#         return a
#
#     options = {
#         (R_Time, R_Power): R_Energy,
#         (R_Current, R_Voltage): R_Power,
#         (R_dimensionless, R_dimensionless): R_dimensionless,
#
#     }
#
#     def search_by_equality(x):
#         for k, v in options.items():
#             if k == x and (k[0].units == x[0].units) and (k[1].units == x[1].units):
#                 return v
#         return None
#
#     o1 = search_by_equality((a, b))
#     if o1 is not None:
#         return o1
#     o2 = search_by_equality((b, a))
#     if o2 is not None:
#         return o2
#
#     msg = 'Cannot find the product of %r with %r.' % (a, b)
#
#     msg += '\nKnown multiplication table:\n'
#     for (m1, m2), res in options.items():
#         msg += '\n   %10s x %10s = %10s' % (m1, m2, res)
#
#     raise ValueError(msg)


# @comptest_fails
# def mult_table_check():
#     mult_table(R_Time, R_Time)



