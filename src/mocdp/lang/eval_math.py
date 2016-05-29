# -*- coding: utf-8 -*-
from .parse_actions import plus_constantsN
from .parts import CDPLanguage
from contracts import contract
from contracts.utils import raise_desc, raise_wrapped
from mocdp.comp.context import CResource, ValueWithUnits
from mocdp.dp import GenericUnary, ProductN, SumN, SumNInt, SumNNat, WrapAMap
from mocdp.exceptions import DPInternalError, DPSemanticError
from mocdp.lang.parse_actions import inv_constant
from mocdp.lang.utils_lists import get_odd_ops, unwrap_list
from mocdp.posets import (Int, Nat, RcompUnits, Space, get_types_universe,
    mult_table, mult_table_seq)
from mocdp.posets.space import Map
from mocdp.dp.dp_sum import sum_dimensionality_works
CDP = CDPLanguage

def eval_constant_divide(op, context):
    from mocdp.lang.eval_constant_imp import eval_constant

    ops = get_odd_ops(unwrap_list(op.ops))
    if len(ops) != 2:
        raise DPSemanticError('divide by more than two')

    constants = [eval_constant(_, context) for _ in ops]
    invs = [inv_constant(_) for _ in constants]
    from mocdp.lang.parse_actions import mult_constantsN
    return mult_constantsN(invs)


@contract(unit1=Space, unit2=Space)
def convert_vu(value, unit1, unit2, context):  # @UnusedVariable
    tu = get_types_universe()
    A_to_B, _ = tu.get_embedding(unit1, unit2)
    return A_to_B(value)


def eval_PlusN_as_constant(x, context):
    return eval_PlusN(x, context, wants_constant=True)


def eval_MultN_as_constant(x, context):
    return eval_MultN(x, context, wants_constant=True)


def eval_MultN_as_rvalue(x, context):
    res = eval_MultN(x, context, wants_constant=False)
    if isinstance(res, ValueWithUnits):
        from mocdp.lang.helpers import get_valuewithunits_as_resource
        return get_valuewithunits_as_resource(res, context)
    else:
        return res


def eval_divide_as_rvalue(op, context):
    from mocdp.lang.eval_resources_imp import eval_rvalue
    from mocdp.lang.eval_constant_imp import NotConstant

    ops = get_odd_ops(unwrap_list(op.ops))

    try:
        from mocdp.lang.eval_constant_imp import eval_constant
        c2 = eval_constant(ops[1], context)
    except NotConstant as e:
        msg = 'Cannot divide by a non-constant.'
        raise_wrapped(DPSemanticError, e, msg, ops[0])

    c2_inv = inv_constant(c2)

    try:
        c1 = eval_constant(ops[0], context)
        # also the first one is a constant
        from mocdp.lang.parse_actions import mult_constantsN

        return mult_constantsN([c1, c2_inv])

    except NotConstant:
        pass

    # then eval as resource
    r = eval_rvalue(ops[0], context)

    res = get_mult_op(context, r=r, c=c2_inv)
    return res



def eval_PlusN_as_rvalue(x, context):
    res = eval_PlusN(x, context, wants_constant=False)
    if isinstance(res, ValueWithUnits):
        from mocdp.lang.helpers import get_valuewithunits_as_resource
        return get_valuewithunits_as_resource(res, context)
    else:
        return res


def flatten_multN(ops):
    res = []
    for op in ops:
        if isinstance(op, CDP.MultN):
            res.extend(flatten_multN(get_odd_ops(unwrap_list(op.ops))))
        else:
            res.append(op)
    return res


def eval_MultN(x, context, wants_constant):
    """ Raises NotConstant if wants_constant is True. """
    from mocdp.lang.parse_actions import mult_constantsN

    assert isinstance(x, CDP.MultN)

    ops = flatten_multN(get_odd_ops(unwrap_list(x.ops)))
    assert len(ops) > 1

    constants = []
    resources = []

    from mocdp.lang.eval_constant_imp import eval_constant
    from mocdp.lang.eval_constant_imp import NotConstant
    for op in ops:

        try:
            x = eval_constant(op, context)
            assert isinstance(x, ValueWithUnits)
            constants.append(x)
        except NotConstant as e:
            if wants_constant:
                msg = 'Product not constant because one op is not constant.'
                raise_wrapped(NotConstant, e, msg, op=op)
            from mocdp.lang.eval_resources_imp import eval_rvalue
            x = eval_rvalue(op, context)
            assert isinstance(x, CResource)
            resources.append(x)

    # it's a constant value
    if len(resources) == 0:
        return mult_constantsN(constants)
    if len(resources) == 1:
        c = mult_constantsN(constants)
        return get_mult_op(context, r=resources[0], c=c)
    else:
        # there are some resources
        resources_types = [context.get_rtype(_) for _ in resources]

        # create multiplication for the resources
        R = mult_table_seq(resources_types)
        dp = ProductN(tuple(resources_types), R)

        from mocdp.lang.helpers import create_operation
        r = create_operation(context, dp, resources,
                             name_prefix='_prod', op_prefix='_factor',
                             res_prefix='_result')

        if not constants:
            return r
        else:
            c = mult_constantsN(constants)
            return get_mult_op(context, r, c)

@contract(r=CResource, c=ValueWithUnits)
def get_mult_op(context, r, c):
    from mocdp.lang.parse_actions import MultValue
    from mocdp.lang.helpers import create_operation
    rtype = context.get_rtype(r)

    # Case 1: rcompunits, rcompunits
    if isinstance(rtype, RcompUnits) and isinstance(c.unit, RcompUnits):
        F = rtype
        R = mult_table(rtype, c.unit)
        function = MultValue(c.value)
        setattr(function, '__name__', '× %s' % (c.unit.format(c.value)))
        dp = GenericUnary(F, R, function)
    elif isinstance(rtype, Nat) and isinstance(c.unit, Nat):
        amap = MultNat(c.value)
        dp = WrapAMap(amap)
    else:
        msg = 'Cannot create multiplication operation.'
        raise_desc(DPInternalError, msg, rtype=rtype, c=c)
    r2 = create_operation(context, dp, resources=[r],
                          name_prefix='_mult', op_prefix='_x',
                          res_prefix='_y')
    return r2

class MultNat(Map):
    @contract(value=int)
    def __init__(self, value):
        self.value = value
        self.N = Nat()
        Map.__init__(self, dom=self.N, cod=self.N)
    def _call(self, x):
        if self.N.equal(self.N.get_top(), x):
            return x
        # TODO: check
        res = x * self.value
        assert isinstance(res, int), res
        return res

class PlusNat(Map):
    @contract(value=int)
    def __init__(self, value):
        self.value = value
        self.N = Nat()
        Map.__init__(self, dom=self.N, cod=self.N)
    def _call(self, x):
        if self.N.equal(self.N.get_top(), x):
            return x
        # TODO: check overflow
        res = x + self.value
        assert isinstance(res, int), res
        return res


def flatten_plusN(ops):
    res = []
    for op in ops:
        if isinstance(op, CDP.PlusN):
            res.extend(flatten_plusN(get_odd_ops(unwrap_list(op.ops))))
        else:
            res.append(op)
    return res

def eval_PlusN(x, context, wants_constant):
    """ Raises NotConstant if wants_constant is True. """
    from .eval_constant_imp import NotConstant, eval_constant
    from .eval_resources_imp import eval_rvalue

    assert isinstance(x, CDP.PlusN)
    assert len(x.ops) > 1

    ops = flatten_plusN(get_odd_ops(unwrap_list(x.ops)))
    constants = []
    resources = []

    for op in ops:
        try:
            x = eval_constant(op, context)
            assert isinstance(x, ValueWithUnits)
            constants.append(x)
        except NotConstant as e:
            if wants_constant:
                msg = 'Product not constant because one op is not constant.'
                raise_wrapped(NotConstant, e, msg, op=op)
            x = eval_rvalue(op, context)
            assert isinstance(x, CResource)
            resources.append(x)

    # it's a constant value
    if len(resources) == 0:
        return plus_constantsN(constants)
    elif len(resources) == 1:
        c = plus_constantsN(constants)
        return get_plus_op(context, r=resources[0], c=c)
    else:
        # there are some resources
        resources_types = [context.get_rtype(_) for _ in resources]

        target_int = Int()
        tu = get_types_universe()
        def castable_to_int(_):
            return tu.leq(_, target_int)

        if all(isinstance(_, RcompUnits) for _ in resources_types):
            # addition between floats
            R = resources_types[0]
            Fs = tuple(resources_types)
            try:
                sum_dimensionality_works(Fs, R)
            except ValueError:
                msg = ''
                for r, rt in zip(resources, resources_types):
                    msg += '- %s has type %s\n' % (r, rt)
                raise_desc(DPSemanticError, 'Incompatible units:\n%s' % msg)

            dp = SumN(Fs, R)
        elif all(isinstance(_, Nat) for _ in resources_types):
            # natural number
            R = Nat()
            dp = SumNNat(tuple(resources_types), R)
        elif all(castable_to_int(_) for _ in resources_types):
            R = Int()
            dp = WrapAMap(SumNInt(tuple(resources_types), R))
        else:
            msg = 'Cannot find sum operator for mixed types.'
            raise_desc(DPInternalError, msg, resources_types=resources_types)

        from mocdp.lang.helpers import create_operation
        r = create_operation(context, dp, resources,
                             name_prefix='_sum', op_prefix='_term',
                             res_prefix='_result')

        if not constants:
            return r
        else:
            c = plus_constantsN(constants)
            return get_plus_op(context, r=r, c=c)

@contract(r=CResource, c=ValueWithUnits)
def get_plus_op(context, r, c):
    from mocdp.lang.parse_actions import PlusValue

    rtype = context.get_rtype(r)

    if isinstance(rtype, RcompUnits) and  isinstance(c.unit, RcompUnits):
        F = rtype
        R = rtype
        function = PlusValue(F=F, R=R, c=c)
        setattr(function, '__name__', '+ %s' % (c.unit.format(c.value)))
        dp = GenericUnary(F, R, function)  # XXX
    elif isinstance(rtype, Nat) and isinstance(c.unit, Nat):
        amap = PlusNat(c.value)
        dp = WrapAMap(amap)
    else:
        msg = 'Cannot create addition operation.'
        raise_desc(DPInternalError, msg, rtype=rtype, c=c)


    # TODO: dp = WrapAMap(map)

    from mocdp.lang.helpers import create_operation
    r2 = create_operation(context, dp, resources=[r],
                          name_prefix='_plus', op_prefix='_x',
                          res_prefix='_y')

    return r2
