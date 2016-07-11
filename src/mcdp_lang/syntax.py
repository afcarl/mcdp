# -*- coding: utf-8 -*-
from .helpers import square
from .parse_actions import (coprod_parse_action, divide_parse_action,
    funshortcut1m, mult_inv_parse_action, mult_parse_action, parse_pint_unit,
    plus_inv_parse_action, plus_parse_action, resshortcut1m,
    space_product_parse_action)
from .parts import CDPLanguage
from .syntax_utils import (COMMA, L, O, S, SCOLON, SCOMMA, SLPAR, SRPAR,
    VariableRef_make, simple_keyword_literal, sp)
from mcdp_lang.utils_lists import make_list
from mocdp.exceptions import mcdp_dev_warning
from pyparsing import (
    CaselessLiteral, Combine, Forward, Group, Keyword, Literal, MatchFirst,
    NotAny, OneOrMore, Optional, Or, ParserElement, Word, ZeroOrMore, alphanums,
    alphas, dblQuotedString, nums, oneOf, opAssoc, operatorPrecedence,
    sglQuotedString)
import math


ParserElement.enablePackrat()

CDP = CDPLanguage


class SyntaxBasics():
    # numbers
    number = Word(nums)
    point = Literal('.')
    e = CaselessLiteral('E')
    plus = Literal('+')
    plusorminus = plus | Literal('-')
    nonneg_integer = sp(Combine(O(plus) + number),
                        lambda t: int(t[0]))
    integer = sp(Combine(O(plusorminus) + number),
                    lambda t: int(t[0]))

    # Note that '42' is not a valid float...
    floatnumber = sp((Combine(integer + point + O(number) + O(e + integer)) |
                      Combine(integer + e + integer)),
                      lambda t: float(t[0]))

    integer_or_float = sp(integer ^ floatnumber,
                          lambda t: CDP.ValueExpr(t[0]))

class SyntaxIdentifiers():
    # unfortunately this needs to be maintained manually
    keywords = [
                'take',
        'load',
        'compact',
        'required',
        'provides',
        'abstract',
        'dp',
        'mcdp',
        'template',
        'sub',
        'for',
        'instance',
        'provided',
        'requires',
        'implemented-by',
        'using',
        'by',
        'catalogue',
        'set-of',
        'mcdp-type',
        'dptype',
        'Nat',
        'Int',
        'pow',
        'approx',
        'approx_lower',
        'approx_upper',
        'Top',
        'Bottom',
        'Maximals',
        'Minimals',
        'finite_poset',
        'choose',
        'flatten',
        'from_library',
        'new',  # = from_library
        'canonical',
        'UpperSets',
        'specialize',
        'with',
        'Uncertain',
        'Interval',
        'product',
        'S',
        'any-of',
        'coproduct',
        'ignore',
    ]

    # remember to .copy() this otherwise things don't work
    _idn = (NotAny(MatchFirst([Keyword(_) for _ in keywords])) +
            Combine(oneOf(list('_' + alphas)) +
                    Optional(Word('_' + alphanums)))).setResultsName('idn')

    @staticmethod
    def get_idn():
        return SyntaxIdentifiers._idn.copy()


class Syntax():
    TOP_LITERAL = 'Top'
    BOTTOM_LITERAL = 'Bottom'


    USING = sp(L('using'), lambda t: CDP.UsingKeyword(t[0]))
    FOR = sp(L('for'), lambda t: CDP.ForKeyword(t[0]))
    # load battery
    LOAD = sp(L('load') | L('`'), lambda t: CDP.LoadKeyword(t[0]))

    SUB = sp(L('sub'), lambda t: CDP.SubKeyword(t[0]))

    TOP = sp(L(TOP_LITERAL) | L('⊤'), lambda t: CDP.TopKeyword(t[0]))
    BOTTOM = sp(L(BOTTOM_LITERAL) | L('⊥'), lambda t: CDP.BottomKeyword(t[0]))

    MCDPTYPE = sp(L('mcdp'), lambda t: CDP.MCDPTypeKeyword(t[0]))

    INSTANCE = sp(Combine(L('instance') + O(L('of'))), lambda t: CDP.InstanceKeyword(t[0]))

    # 'MATHEMATICAL LEFT ANGLE BRACKET' (U+27E8) ⟨
    # 'MATHEMATICAL RIGHT ANGLE BRACKET'   ⟩
# ⟨⟩
    OPEN_BRACE = sp(L('<') ^ L('⟨'), lambda t: CDP.OpenBraceKeyword(t[0]))
    CLOSE_BRACE = sp(L('>') ^ L('⟩'), lambda t: CDP.CloseBraceKeyword(t[0]))
    REQUIRED_BY = sp((L('required') | L('req.')) - L('by'),
                    lambda _: CDP.RequiredByKeyword('required by'))
    mcdp_dev_warning('these variations are not tested')
    PROVIDED_BY = sp((L('provided') | L('prov.')) - L('by'),
                    lambda _: CDP.ProvidedByKeyword('provided by'))

    PROVIDED = sp(L('provided'), lambda _: CDP.ProvidedKeyword('provided'))
    REQUIRED = sp(L('required'), lambda _: CDP.ProvidedKeyword('required'))


    GEQ = sp(L('>=') | L('≥') | L('⊇') | L('≽') | L('⊒'), lambda t: CDP.geq(t[0]))
    LEQ = sp(L('<=') | L('≤') | L('⊆') | L('≼') | L('⊑'), lambda t: CDP.leq(t[0]))

    EXPONENT = sp(L('^'), lambda t: CDP.exponent(t[0]))

    EQ = sp(L('='), lambda t: CDP.eq(t[0]))
    DOT = sp(L('.'), lambda t: CDP.DotPrep(t[0]))
    PLUS = sp(L('+'), lambda t: CDP.plus(t[0]))
    TIMES = sp(L('*'), lambda t: CDP.times(t[0]))
    BAR = sp(L('/'), lambda t: CDP.bar(t[0]))

    CDPTOKEN = sp(L('mcdp'), lambda t: CDP.MCDPKeyword(t[0]))


    FROM_LIBRARY = sp(L('from_library') | L('new'), lambda t: CDP.FromLibraryKeyword(t[0]))

    COPROD = sp(L('^'), lambda t: CDP.coprod(t[0]))

    # "call"
    C = lambda x, b: x.setResultsName(b)

    # optional whitespace
    ow = S(ZeroOrMore(L(' ')))
 
    # do not load earlier
    from .syntax_codespec import get_code_spec_expr
    code_spec = get_code_spec_expr()

    pint_unit_base = NotAny(oneOf(SyntaxIdentifiers.keywords + ['x'])) + Word(alphas + '$')

    pint_unit_power = L('^') + Word(nums)
    pint_unit_simple = pint_unit_base + O(pint_unit_power)
    pint_unit_connector = L('/') | L('*')
 
    space_pint_unit = sp((pint_unit_simple + ZeroOrMore(pint_unit_connector + pint_unit_simple)),
                   parse_pint_unit)

    space = Forward() 
    constant_value = Forward()


    get_idn = SyntaxIdentifiers.get_idn
    # "load <name>"
    name_poset = sp(get_idn(), lambda t: CDP.PosetName(t[0]))
    load_poset = sp(LOAD - name_poset, lambda t: CDP.LoadPoset(t[0], t[1]))

    # UpperSets(<poset>)
    UPPERSETS = sp(L('UpperSets'), lambda t: CDP.UpperSetsKeyword(t[0]))
    space_uppersets = sp(UPPERSETS + SLPAR + space + SRPAR,
                   lambda t: CDP.MakeUpperSets(t[0], t[1]))

    # finite_poset {
    #     a
    #     b  c  d  e
    #
    #     a <= b <= c
    #   }
    #
    # evaluates to CDP.FinitePoset
    FINITE_POSET = sp(L('finite_poset'), lambda t: CDP.FinitePosetKeyword(t[0]))
    finite_poset_el = sp(get_idn(), lambda t: CDP.FinitePosetElement(t[0]))
    finite_poset_chain = sp(finite_poset_el + ZeroOrMore(LEQ + finite_poset_el),
                               lambda t: make_list(t))

    space_finite_poset = sp(FINITE_POSET + S(L('{')) + ZeroOrMore(finite_poset_chain) + S(L('}')),
                      lambda t: CDP.FinitePoset(t[0], make_list(t[1:])))

    space_powerset_keyword = sp(L('℘') | L('set-of'), lambda t: CDP.PowerSetKeyword(t[0]))
    space_powerset = sp(space_powerset_keyword - L('(') + space + L(')'),
                        lambda t: CDP.PowerSet(t[0], t[1],
                                               t[2], t[3]))

    PRODUCTWITHLABELS = sp(L('product'), lambda t: CDP.ProductKeyword(t[0]))
    space_product_label = sp(get_idn(), lambda t: CDP.ProductWithLabelsLabel(t[0]))
    space_product_entry = space_product_label + SCOLON + space
    space_product_with_labels = sp(PRODUCTWITHLABELS + SLPAR + O(space_product_entry) +
                                   ZeroOrMore(SCOMMA + space_product_entry) + SRPAR,
                                   lambda t: 
                                   CDP.ProductWithLabels(keyword=t[0],
                                                         entries=make_list(t[1:])))
    COPRODUCT = sp(L('coproduct'), lambda t: CDP.SpaceCoproductKeyword(t[0]))
    space_coproduct_label = sp(get_idn(), lambda t: CDP.ProductWithLabelsLabel(t[0]))
    space_coproduct_entry = space_product_label + SCOLON + space
    space_coproduct = sp(COPRODUCT + SLPAR +
                         O(space) + ZeroOrMore(SCOMMA + space) + SRPAR,
                           lambda t:
                                   CDP.SpaceCoproduct(keyword=t[0],
                                                      entries=make_list(t[1:])))


    INTERVAL = sp(L('Interval'), lambda t: CDP.IntervalKeyword(t[0]))
    
    space_interval = sp(INTERVAL + SLPAR + constant_value + SCOMMA + constant_value + SRPAR,
                        lambda t: CDP.SpaceInterval(keyword=t[0], a=t[1], b=t[2]))
    
    space_nat = sp(L('Nat') | L('ℕ'), lambda t: CDP.Nat(t[0]))
    space_int = sp(L('Int') | L('ℤ'), lambda t: CDP.Int(t[0]))


#     SingleElementPosetKeyword = namedtuplewhere('SingleElementPosetKeyword', 'keyword')
#     SingleElementPosetTag = namedtuplewhere('SingleElementPosetTag', 'value')
#     SingleElementPoset = namedtuplewhere('SingleElementPoset', 'keyword tag')
    space_single_element_poset_tag = sp(get_idn(), lambda t: CDP.SingleElementPosetTag(t[0]))
    space_single_element_poset_keyword = sp(L('S'), lambda t: CDP.SingleElementPosetKeyword(t[0]))
    space_single_element_poset = sp(space_single_element_poset_keyword +
                                    SLPAR + space_single_element_poset_tag + SRPAR,
                              lambda t: CDP.SingleElementPoset(t[0], t[1]))

    space_operand = (space_pint_unit ^
                     space_powerset ^
                     space_nat ^
                     space_int ^
                     load_poset ^
                     code_spec ^
                     space_finite_poset
                     ^ space_uppersets
                     ^ space_interval
                     ^ space_product_with_labels
                     ^ space_single_element_poset
                     ^ space_coproduct
                     )


    PRODUCT = sp(L('x') | L('×'), lambda t: CDP.product(t[0]))
    space << operatorPrecedence(space_operand, [
        (PRODUCT, 2, opAssoc.LEFT, space_product_parse_action),
    ])


    unitst = S(L('[')) + C(space, 'unit') + S(L(']'))


    nat_constant = sp(L('nat') + L(':') + SyntaxBasics.nonneg_integer,
                      lambda t: CDP.NatConstant(t[0], t[1], t[2]))

    int_constant = sp(L('int') + L(':') + SyntaxBasics.integer,
                      lambda t: CDP.IntConstant(t[0], t[1], t[2]))

    fname = sp(get_idn(), lambda t: CDP.FName(t[0]))
    rname = sp(get_idn(), lambda t: CDP.RName(t[0]))

    PROVIDES = sp(L('provides'), lambda t: CDP.ProvideKeyword(t[0]))
    fun_statement = sp(PROVIDES + C(fname, 'fname') + unitst,
                       lambda t: CDP.FunStatement(t[0], t[1], t[2]))

    REQUIRES = sp(L('requires'), lambda t: CDP.RequireKeyword(t[0]))
    res_statement = sp(REQUIRES + C(rname, 'rname') + unitst,
                       lambda t: CDP.ResStatement(t[0], t[1], t[2]))

    number_with_unit1 = sp(SyntaxBasics.integer_or_float + unitst,
                           lambda t: CDP.SimpleValue(t[0], t[1]))

    dimensionless = sp(L('[') + L(']'), lambda _: CDP.RcompUnit('m/m'))
    number_with_unit2 = sp(SyntaxBasics.integer_or_float + dimensionless,
                           lambda t: CDP.SimpleValue(t[0], t[1]))
    
    number_with_unit3 = sp(SyntaxBasics.integer_or_float + space,
                           lambda t: CDP.SimpleValue(t[0], t[1]))

    number_with_unit4_top = sp(TOP + space,
                               lambda t: CDP.Top(t[0], t[1]))

    number_with_unit5_bot = sp(BOTTOM + space,
                               lambda t: CDP.Bottom(t[0], t[1]))
    MINIMALS = sp(L('Minimals'), lambda t: CDP.MinimalsKeyword(t[0]))
    number_with_unit_minimals = sp(MINIMALS + space,
                                   lambda t: CDP.Minimals(t[0], t[1]))
    MAXIMALS = sp(L('Maximals'), lambda t: CDP.MaximalsKeyword(t[0]))
    number_with_unit_maximals = sp(MAXIMALS + space,
                                   lambda t: CDP.Maximals(t[0], t[1]))

    number_with_unit = (number_with_unit1 ^
                        number_with_unit2 ^
                        number_with_unit3 ^
                        number_with_unit4_top ^
                        number_with_unit5_bot ^
                        number_with_unit_minimals ^
                        number_with_unit_maximals)

    # TODO: change

    # a quoted string
    quoted = sp(dblQuotedString | sglQuotedString, lambda t:t[0][1:-1])
    ndpname = sp(get_idn() | quoted, lambda t: CDP.NDPName(t[0]))

    ndpt_load = sp(LOAD - (ndpname | SLPAR - ndpname - SRPAR),
                        lambda t: CDP.LoadNDP(t[0], t[1]))

    # An expression that evaluates to a NamedDP
    ndpt_dp_rvalue = Forward()
    template = Forward()

    # <dpname> = ...
    dpname = sp(get_idn(), lambda t: CDP.DPName(t[0]))
    dptypename = sp(get_idn(), lambda t: CDP.DPTypeName(t[0]))

    dpinstance_from_type = sp((INSTANCE + ndpt_dp_rvalue) ^
                              (INSTANCE + SLPAR + ndpt_dp_rvalue + SRPAR),
                              lambda t: CDP.DPInstance(t[0], t[1]))

    dpinstance_from_library_shortcut = \
        sp(FROM_LIBRARY + (ndpname | (SLPAR - ndpname + SRPAR)),
                    lambda t:CDP.DPInstanceFromLibrary(t[0], t[1]))

    dpinstance_expr = dpinstance_from_type ^ dpinstance_from_library_shortcut

    setsub_expr = sp(SUB - dpname - S(L('=')) - dpinstance_expr,
                     lambda t: CDP.SetName(t[0], t[1], t[2]))

    setsub_expr_implicit = sp(dpname - S(L('=')) - dpinstance_expr,
                     lambda t: CDP.SetName(None, t[0], t[1]))

    setmcdptype_expr = sp(MCDPTYPE - dptypename - L('=') - ndpt_dp_rvalue,
                     lambda t: CDP.SetMCDPType(t[0], t[1], t[2], t[3]))

    setmcdptype_expr_implicit = sp(dptypename - L('=') - ndpt_dp_rvalue,
                     lambda t: CDP.SetMCDPType(None, t[0], t[1], t[2]))

    # An expression that evaluates to a resource
    rvalue = Forward()
    # An expression that evaluates to a function
    fvalue = Forward()

    # For pretty printing
    ELLIPSIS = sp(L('...'), lambda t: CDP.Ellipsis(t[0]))
    setname_rightside = ELLIPSIS | rvalue  # ^ dp_rvalue
 
    setname_generic_var = sp(get_idn(),
                              lambda t: CDP.SetNameGenericVar(t[0]))

    # a = ...
    # a = 10 g
    setname_generic = sp(setname_generic_var + EQ + setname_rightside,
                         lambda t: CDP.SetNameGeneric(t[0], t[1], t[2]))

    setname_fvalue = sp(setname_generic_var + EQ + fvalue,
                        lambda t: CDP.SetNameFValue(t[0], t[1], t[2]))

    variable_ref = sp(get_idn(), VariableRef_make)

    ndpt_dp_variable_ref = sp(get_idn(), lambda t: CDP.DPVariableRef(t[0]))
    

    # solve( <0 g>, `model )
    SOLVE = sp(L('solve'), lambda t: CDP.SolveModelKeyword(t[0]))
    solve_model = sp(SOLVE + SLPAR + constant_value + SCOMMA + ndpt_dp_rvalue + SRPAR,
               lambda t: CDP.SolveModel(keyword=t[0], f=t[1], model=t[2]))


    tuple_of_constants = sp(OPEN_BRACE + O(constant_value +
                            ZeroOrMore(COMMA + constant_value)) + CLOSE_BRACE,
                            lambda t: CDP.MakeTuple(t[0], make_list(list(t)[1:-1], where=t[0].where), t[-1]))

    rvalue_make_tuple = sp(OPEN_BRACE + rvalue +
                    ZeroOrMore(COMMA + rvalue) + CLOSE_BRACE,
                    lambda t: CDP.MakeTuple(t[0], make_list(list(t)[1:-1]), t[-1]))
    
    # TODO: how to express empty typed list? "{g}"
    collection_of_constants = sp(S(L('{')) + constant_value +
                                 ZeroOrMore(COMMA + constant_value) + S(L('}')),
                                 lambda t: CDP.Collection(make_list(list(t))))

    upper_set_from_collection_keyword = sp(L('upperclosure'), lambda t: CDP.UpperSetFromCollectionKeyword(t[0]))
    upper_set_from_collection = sp(upper_set_from_collection_keyword + collection_of_constants,
                   lambda t: CDP.UpperSetFromCollection(t[0], t[1]))

    # <space> : identifier
    # `plugs : european
    short_identifiers = Word(nums + alphas + '_')
    space_custom_value1 = sp(space + L(":") + (short_identifiers ^ L('*')),
                          lambda t: CDP.SpaceCustomValue(t[0], t[1], t[2]))

    constant_value << (number_with_unit
                       ^ variable_ref
                       ^ collection_of_constants
                        ^ tuple_of_constants
                       ^ nat_constant
                       ^ int_constant
                       ^ upper_set_from_collection
                       ^ space_custom_value1
                       ^ solve_model)

    rvalue_resource_simple = sp(dpname + DOT - rname,
                                lambda t: CDP.Resource(s=t[2], keyword=t[1], dp=t[0]))
                     
    rvalue_resource_fancy = sp(rname + REQUIRED_BY - dpname,
                               lambda t: CDP.Resource(s=t[0], keyword=t[1], dp=t[2]))

    rvalue_resource = rvalue_resource_simple ^ rvalue_resource_fancy

    rvalue_new_function = sp(get_idn(), VariableRef_make)
    rvalue_new_function2 = sp(PROVIDED + get_idn(),
                              lambda t: CDP.NewFunction(t[1]))
    ANYOF = sp(L('any-of'), lambda t: CDP.AnyOfKeyword(t[0]))
    rvalue_any_of = sp(ANYOF + SLPAR + constant_value + SRPAR,
                       lambda t: CDP.AnyOfRes(t[0], t[1]))
    fvalue_any_of = sp(ANYOF + SLPAR + constant_value + SRPAR,
                       lambda t: CDP.AnyOfFun(t[0], t[1]))

    # Uncertain(<lower>, <upper>)
    UNCERTAIN = sp(L('Uncertain'), lambda t: CDP.UncertainKeyword(t[0]))
    rvalue_uncertain = sp(UNCERTAIN + SLPAR + rvalue + SCOMMA + rvalue + SRPAR,
                          lambda t: CDP.UncertainRes(keyword=t[0], lower=t[1], upper=t[2]))

    fvalue_uncertain = sp(UNCERTAIN + SLPAR + fvalue + SCOMMA + fvalue + SRPAR,
                          lambda t: CDP.UncertainFun(keyword=t[0], lower=t[1], upper=t[2]))

    # oops, infinite recursion
#     rvalue_tuple_indexing = sp(rvalue + S(L('[')) + SyntaxBasics.integer + S(L(']')),
#                                lambda t: CDP.TupleIndex(value=t[0], index=t[1]))

    # take(<a, b>, 0)
    TAKE = sp(L('take') | L('`'), lambda t: CDP.TakeKeyword(t[0]))
    rvalue_tuple_indexing = sp(TAKE + SLPAR + rvalue + SCOMMA +
                                  SyntaxBasics.integer + SRPAR,
                               lambda t: CDP.TupleIndex(keyword=t[0], value=t[1], index=t[2]))

    TAKEF = sp(L('take') | L('`'), lambda t: CDP.TakeKeyword(t[0]))
    lf_tuple_indexing = sp(TAKEF + SLPAR + fvalue + SCOMMA +
                                  SyntaxBasics.integer + SRPAR,
                               lambda t: CDP.TupleIndexFun(keyword=t[0], value=t[1], index=t[2]))

    ICOMMA = L('..')
    index_label = sp(get_idn(), lambda t: CDP.IndexLabel(t[0]))
    # rvalue instead of rvalue_new_function
    rvalue_label_indexing = sp(rvalue_new_function + S(ICOMMA) + index_label,
                               lambda t: CDP.ResourceLabelIndex(rvalue=t[0], label=t[1]))


    fvalue_disambiguation_tag = sp(Combine(L('(') + L('f') + L(')')),
                                   lambda t: CDP.DisambiguationFunTag(t[0]))

    fvalue_disambiguation = sp(fvalue_disambiguation_tag + fvalue,
                               lambda t: CDP.DisambiguationFun(tag=t[0], fvalue=t[1]))

    fvalue_new_resource = sp(get_idn(),
                             lambda t: CDP.NewResource(t[0]))

    fvalue_new_resource2 = sp(REQUIRED + get_idn(),
                              lambda t: CDP.NewResource(t[1]))

    fvalue_label_indexing = sp(fvalue_new_resource + S(ICOMMA) + index_label,
                               lambda t: CDP.FunctionLabelIndex(fvalue=t[0], label=t[1]))

    unary = {
        'sqrt': lambda op1: CDP.GenericNonlinearity(math.sqrt, op1, lambda F: F),
        'ceil': lambda op1: CDP.GenericNonlinearity(math.ceil, op1, lambda F: F),
        'square': lambda op1: CDP.GenericNonlinearity(square, op1, lambda F: F),
    }

    unary_op = Or([L(x) for x in unary])
    rvalue_unary_expr = sp((C(unary_op, 'opname') - SLPAR
                    + C(rvalue, 'op1')) - SRPAR,
                    lambda t: Syntax.unary[t['opname']](t['op1']))

    binary = {
        'max': CDP.OpMax,
        'min': CDP.OpMin,
    }

    opname = sp(Or([L(x) for x in binary]), lambda t: CDP.OpKeyword(t[0]))

    rvalue_binary = sp((opname - SLPAR +
                    C(rvalue, 'op1') - SCOMMA
                    + C(rvalue, 'op2')) - SRPAR ,
                       lambda t: Syntax.binary[t[0].keyword](a=t['op1'], b=t['op2'], keyword=t[0]))

    fvalue_simple = sp(dpname + DOT - fname,
                       lambda t: CDP.Function(dp=t[0], s=t[2], keyword=t[1]))

    fvalue_fancy = sp(fname + PROVIDED_BY - dpname,
                      lambda t: CDP.Function(dp=t[2], s=t[0], keyword=t[1]))

    fvalue_function = fvalue_simple ^ fvalue_fancy

    fvalue_maketuple = sp(OPEN_BRACE + fvalue + ZeroOrMore(COMMA + fvalue) + CLOSE_BRACE,
                       lambda t: CDP.MakeTuple(t[0], make_list(list(t)[1:-1]), t[-1]))


    # Fractions

    integer_fraction = sp(SyntaxBasics.integer + S(L('/')) + SyntaxBasics.integer,
                          lambda t: CDP.IntegerFraction(num=t[0], den=t[1]))

    integer_fraction_one = sp(SyntaxBasics.integer.copy(),
                              lambda t: CDP.IntegerFraction(num=int(t[0]), den=1))

    rat_power_exponent = integer_fraction | integer_fraction_one

    rvalue_power_expr_1 = sp((S(L('pow')) - SLPAR - C(rvalue, 'op1') - L(',')  # the glyph
                              + C(rat_power_exponent, 'exponent')) - SRPAR,
                             lambda t: CDP.Power(op1=t[0], glyph=None, exponent=t[2]))

    rvalue_power_expr_2 = sp((rvalue_resource ^ rvalue_new_function)
                             + EXPONENT - rat_power_exponent,
                             lambda t: CDP.Power(op1=t[0], glyph=t[1], exponent=t[2]))

    rvalue_power_expr = rvalue_power_expr_1 ^ rvalue_power_expr_2

    constraint_expr_geq = sp(fvalue + GEQ - rvalue,
                             lambda t: CDP.Constraint(function=t[0],
                                                      rvalue=t[2],
                                                      prep=t[1]))

    constraint_expr_leq = sp(rvalue + LEQ - fvalue,
                             lambda t: CDP.Constraint(function=t[2],
                                                      rvalue=t[0],
                                                      prep=t[1]))

    fun_shortcut1 = sp(PROVIDES + fname + USING + dpname,
                       lambda t: CDP.FunShortcut1(provides=t[0],
                                                  fname=t[1],
                                                  prep_using=t[2],
                                                  name=t[3]))

    res_shortcut1 = sp(REQUIRES + rname + FOR + dpname,
                       lambda t: CDP.ResShortcut1(t[0], t[1], t[2], t[3]))

    fun_shortcut2 = sp(PROVIDES + fname + LEQ - fvalue,
                       lambda t: CDP.FunShortcut2(t[0], t[1], t[2], t[3]))

    res_shortcut2 = sp(REQUIRES + rname + GEQ - rvalue,
                       lambda t: CDP.ResShortcut2(t[0], t[1], t[2], t[3]))

    fun_shortcut3 = sp(PROVIDES +
                       C(Group(fname + OneOrMore(S(L(',')) + fname)), 'fnames')
                       + USING + dpname,
                       lambda t: funshortcut1m(provides=t[0],
                                               fnames=make_list(list(t['fnames'])),
                                               prep_using=t[2],
                                               name=t[3]))

    res_shortcut3 = sp(REQUIRES +
                       C(Group(rname + OneOrMore(S(L(',')) + rname)), 'rnames')
                       + FOR + dpname,
                       lambda t: resshortcut1m(requires=t[0],
                             rnames=make_list(list(t['rnames'])),
                             prep_for=t[2],
                             name=t[3]))

    IGNORE = sp(L('ignore'), lambda t: CDP.IgnoreKeyword(t[0]))
    ignore_fun = sp(IGNORE + fvalue_function,
                    lambda t: CDP.IgnoreFun(t[0], t[1]))
    ignore_res = sp(IGNORE + rvalue_resource,
                    lambda t: CDP.IgnoreRes(t[0], t[1]))

    line_expr = (constraint_expr_geq ^ 
                 constraint_expr_leq ^
                     (setname_generic ^ 
                      setname_fvalue ^
                      setsub_expr ^ 
                      setsub_expr_implicit ^ 
                      setmcdptype_expr ^ 
                      setmcdptype_expr_implicit)
                 ^ fun_statement ^ res_statement ^ fun_shortcut1 ^ fun_shortcut2
                 ^ res_shortcut1 ^ res_shortcut2 ^ res_shortcut3 ^ fun_shortcut3
                 ^ ignore_res
                 ^ ignore_fun)

    dp_model_statements = sp(ZeroOrMore(S(ow) + line_expr),
                             lambda t: make_list(list(t)))

    DPTOKEN = sp(L('dp'), lambda t: CDP.DPWrapToken(t[0]))
    ndpt_dp_model = sp(CDPTOKEN - S(L('{')) - dp_model_statements - S(L('}')),
                  lambda t: CDP.BuildProblem(keyword=t[0], statements=t[1]))

    # load
    primitivedp_name = sp(get_idn(), lambda t: CDP.FuncName(t[0]))  # XXX
    primitivedp_load = sp(LOAD - primitivedp_name, lambda t: CDP.LoadDP(t[0], t[1]))

    primitivedp_expr = (primitivedp_load ^
                        code_spec)

    simple_dp_model_stats = sp(ZeroOrMore(S(ow) + fun_statement ^ res_statement),
                               lambda t: make_list(list(t)))

    IMPLEMENTEDBY = sp(L('implemented-by'), lambda t: CDP.ImplementedbyKeyword(t[0]))
    ndpt_simple_dp_model = sp(DPTOKEN -
                         S(L('{')) -
                         simple_dp_model_stats -
                         IMPLEMENTEDBY -
                         primitivedp_expr -
                         S(L('}')),
                         lambda t: CDP.DPWrap(token=t[0], statements=t[1],
                                              prep=t[2], impl=t[3]))

    entry = rvalue
    imp_name = sp(get_idn(), lambda t: CDP.ImpName(t[0]))
    col_separator = L('|') ^ L('│')  # box drawing
    catalogue_row = sp(imp_name +
                       ZeroOrMore(S(col_separator) + entry),
                       lambda t: make_list(list(t)))

    catalogue_table = sp(OneOrMore(catalogue_row),
                         lambda t: CDP.CatalogueTable(make_list(list(t))))

    FROMCATALOGUE = sp(L('catalogue'), lambda t:CDP.FromCatalogueKeyword(t[0]))
    ndpt_catalogue_dp = sp(FROMCATALOGUE -
                      S(L('{')) -
                      simple_dp_model_stats -
                      catalogue_table -
                      S(L('}')),
                      lambda t: CDP.FromCatalogue(t[0], t[1], t[2]))
    # Example:
    #    choose(name: <dp>, name2: <dp>)
    CHOOSE = simple_keyword_literal('choose', CDP.CoproductWithNamesChooseKeyword)
    ndpt_coproduct_with_names_name = \
        sp(get_idn(), lambda t: CDP.CoproductWithNamesName(t[0]))
    # ndpt_coproduct_with_names_one = ndpt_coproduct_with_names_name + SCOLON + ndpt_dp_rvalue
    ndpt_coproduct_with_names_one = ndpt_coproduct_with_names_name + SCOLON + (ndpt_dp_rvalue | dpinstance_expr)
    ndpt_coproduct_with_names = sp(CHOOSE - SLPAR + ndpt_coproduct_with_names_one
                                    + ZeroOrMore(SCOMMA + ndpt_coproduct_with_names_one) 
                                    - SRPAR,
                                    lambda t: CDP.CoproductWithNames(keyword=t[0],
                                                                     elements=make_list(t[1:])))
    
    # Example:
    #   approx(mass,0%,0g,%)
    APPROX = sp(L('approx'), lambda t: CDP.ApproxKeyword(t[0]))
    ndpt_approx = sp(APPROX - S(L('(')) - fname + S(COMMA)
                         - SyntaxBasics.integer_or_float - S(L('%'))
                         - S(COMMA) + constant_value  # step
                         - S(COMMA) + constant_value  # max value
                        - S(L(')')) - ndpt_dp_rvalue,
                         lambda t: CDP.ApproxDPModel(keyword=t[0],
                                                     name=t[1],
                                                     perc=t[2],
                                                     abs=t[3],
                                                     max_value=t[4],
                                                     dp=t[5]))



    ABSTRACT = sp(L('abstract'), lambda t: CDP.AbstractKeyword(t[0]))
    ndpt_abstract = sp(ABSTRACT - ndpt_dp_rvalue,
                       lambda t: CDP.AbstractAway(t[0], t[1]))
    
    COMPACT = sp(L('compact'), lambda t: CDP.CompactKeyword(t[0]))
    ndpt_compact = sp(COMPACT - ndpt_dp_rvalue,
                       lambda t: CDP.Compact(t[0], t[1]))

    TEMPLATE = sp(L('template'), lambda t: CDP.TemplateKeyword(t[0]))
    ndpt_template = sp(TEMPLATE - ndpt_dp_rvalue,
                       lambda t: CDP.MakeTemplate(t[0], t[1]))

    FLATTEN = sp(L('flatten'), lambda t: CDP.FlattenKeyword(t[0]))
    ndpt_flatten = sp(FLATTEN - ndpt_dp_rvalue,
                      lambda t: CDP.Flatten(t[0], t[1]))

    CANONICAL = sp(L('canonical'), lambda t: CDP.FlattenKeyword(t[0]))
    ndpt_canonical = sp(CANONICAL - ndpt_dp_rvalue,
                            lambda t: CDP.MakeCanonical(t[0], t[1]))

    APPROX_LOWER = sp(L('approx_lower'), lambda t: CDP.ApproxLowerKeyword(t[0]))
    ndpt_approx_lower = sp(APPROX_LOWER - SLPAR + SyntaxBasics.integer +
                            SCOMMA + ndpt_dp_rvalue + SRPAR,
                       lambda t: CDP.ApproxLower(t[0], t[1], t[2]))

    APPROX_UPPER = sp(L('approx_upper'), lambda t: CDP.ApproxUpperKeyword(t[0]))
    ndpt_approx_upper = sp(APPROX_UPPER - SLPAR + SyntaxBasics.integer +
                            SCOMMA + ndpt_dp_rvalue + SRPAR,
                       lambda t: CDP.ApproxUpper(t[0], t[1], t[2]))


    template_load = sp(LOAD - (ndpname | SLPAR - ndpname - SRPAR),   
                       lambda t: CDP.LoadTemplate(t[0], t[1]))
    
    template_spec_param_name = sp(get_idn(), lambda t: CDP.TemplateParamName(t[0]))
    template_spec_param = template_spec_param_name + S(L(':')) + ndpt_dp_rvalue
    parameters = O(template_spec_param) + ZeroOrMore(SCOMMA + template_spec_param)
    LSQ = sp(L('['), lambda t: CDP.LSQ(t[0]))
    RSQ = sp(L(']'), lambda t: CDP.RSQ(t[0]))

    template_spec = sp(TEMPLATE - LSQ + Group(parameters) + RSQ
                       + ndpt_dp_rvalue,
                       lambda t: CDP.TemplateSpec(keyword=t[0],
                                                  params=make_list(t[2], t[1].where),
                                                  ndpt=t[4]))
    template << (code_spec | template_load | template_spec)

    SPECIALIZE = sp(L('specialize'), lambda t: CDP.SpecializeKeyword(t[0]))

    ndpt_specialize = sp(SPECIALIZE + LSQ + Group(parameters) + RSQ + template,
                         lambda t: CDP.Specialize(keyword=t[0],
                                                  params=make_list(t[2], t[1].where),
                                                  template=t[4]))

    ndpt_dp_operand = (
        code_spec |
        ndpt_load |
        ndpt_simple_dp_model |
        ndpt_dp_model |
        ndpt_abstract |
        ndpt_template |
        ndpt_compact |
        ndpt_catalogue_dp |
        ndpt_approx_lower |
        ndpt_approx_upper |
        ndpt_approx |
        ndpt_coproduct_with_names |
        ndpt_flatten |
        ndpt_canonical |
        ndpt_dp_variable_ref |
        ndpt_specialize
    )

    ndpt_dp_rvalue << operatorPrecedence(ndpt_dp_operand, [
    #     ('-', 1, opAssoc.RIGHT, Unary.parse_action),
        (COPROD, 2, opAssoc.LEFT, coprod_parse_action),
    ])

    # I could put "rvalue" here, but then I get a recursive
    rvalue_operand = (rvalue_new_function ^
                       rvalue_new_function2 ^
                       rvalue_resource ^
                       rvalue_binary ^
                       rvalue_unary_expr ^
                       constant_value ^
                       rvalue_power_expr ^
                       rvalue_tuple_indexing ^
                       rvalue_make_tuple ^
                       rvalue_uncertain ^
                       rvalue_label_indexing
                       ^ rvalue_any_of)

    rvalue << operatorPrecedence(rvalue_operand, [
        (TIMES, 2, opAssoc.LEFT, mult_parse_action),
        (BAR, 2, opAssoc.LEFT, divide_parse_action),
        (PLUS, 2, opAssoc.LEFT, plus_parse_action),
    ])

    fvalue_operand = (constant_value ^
        fvalue_simple ^
        fvalue_fancy ^
        fvalue_new_resource ^
        fvalue_new_resource2 ^
        fvalue_maketuple ^
        fvalue_uncertain ^
        fvalue_disambiguation ^
        fvalue_label_indexing ^
        lf_tuple_indexing
        ^ fvalue_any_of
        ^ (SLPAR - (constant_value ^ fvalue_simple ^ fvalue_fancy ^
                      fvalue_new_resource ^ fvalue_new_resource2 ^ fvalue_maketuple
                      ^ fvalue_uncertain
                      ^ fvalue_disambiguation
                      ^ fvalue_label_indexing
                    ^ lf_tuple_indexing
                    ^ fvalue_any_of
                      ) - SRPAR))

    fvalue << operatorPrecedence(fvalue_operand, [
        ('*', 2, opAssoc.LEFT, mult_inv_parse_action),
        ('+', 2, opAssoc.LEFT, plus_inv_parse_action),
    ])
