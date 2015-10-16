# -*- coding: utf-8 -*-
from .parts import (Constraint, FunStatement, LoadCommand, Mult, NewFunction,
    ResStatement, Resource, SetName)
from contracts import contract
from contracts.interface import Where
from contracts.utils import indent, raise_wrapped
from mocdp.comp.interfaces import NamedDP
from mocdp.exceptions import DPInternalError, DPSemanticError, DPSyntaxError
from mocdp.lang.parts import (
    DPWrap, Function, LoadDP, NewResource, OpMax, OpMin, PDPCodeSpec, Plus)
from mocdp.lang.utils import parse_action
from mocdp.posets.rcomp import (R_Cost, R_Current, R_Energy, R_Power, R_Time,
    R_Voltage, R_Weight, R_dimensionless)
from pyparsing import (Combine, Forward, Group, LineEnd, LineStart, Literal,
    Optional, Or, ParseException, ParseFatalException, ParserElement, SkipTo,
    Suppress, Word, ZeroOrMore, alphanums, alphas, oneOf, opAssoc,
    operatorPrecedence)
import string

ParserElement.enablePackrat()

# ParserElement.setDefaultWhitespaceChars('')

# shortcuts
S = Suppress
L = Literal
C = lambda x, b: x.setResultsName(b)
def spa(x, b):
    @parse_action
    def p(tokens, loc, s):
        where = Where(s, loc)
        try:
            res = b(tokens)
        except BaseException as e:
            print e
            raise_wrapped(DPInternalError, e, "Error while parsing.", where=where.__str__(),
                          tokens=tokens)
        res.where = where
        return res
    x.setParseAction(p)


ow = S(ZeroOrMore(L(' ')))
EOL = S(LineEnd())
line = SkipTo(LineEnd(), failOn=LineStart() + LineEnd())


# identifier
idn = Combine(oneOf(list(alphas)) + Optional(Word('_' + alphanums)))


# Simple DPs being wrapped
#
# f name (unit)
# f name (unit)
# wraps name

units = {
    'J': R_Energy,
    's': R_Time,
    'A': R_Current,
    'V': R_Voltage,
    'g': R_Weight,
    'W': R_Power,
    '$': R_Cost,
    'R': R_dimensionless,
}
unit_expr = oneOf(list(units))
spa(unit_expr, lambda t: units[t[0]])

unitst = S(L('[')) + C(unit_expr, 'unit') + S(L(']'))
fun_statement = S(L('F')) ^ S(L('provides')) + C(idn, 'fname') + unitst
spa(fun_statement, lambda t: FunStatement(t['fname'], t['unit']))

res_statement = S(L('R')) ^ S(L('requires')) + C(idn, 'rname') + unitst
spa(res_statement, lambda t: ResStatement(t['rname'], t['unit']))



# load battery
load_expr = S(L('load')) + C(idn, 'load_arg')
spa(load_expr, lambda t: LoadCommand(t['load_arg']))

dp_rvalue = Forward()
# <dpname> = ...
setname_expr = C(idn, 'dpname') + S(L('=')) + C(dp_rvalue, 'rvalue')
spa(setname_expr, lambda t: SetName(t['dpname'], t['rvalue']))

rvalue = Forward()
rvalue_resource_simple = C(idn, 'dp') + S(L('.')) + C(idn, 's')

prep = (S(L('required')) + S(L('by'))) | S(L('of'))
rvalue_resource_fancy = C(idn, 's') + prep + C(idn, 'dp')
rvalue_resource = rvalue_resource_simple | rvalue_resource_fancy
spa(rvalue_resource, lambda t: Resource(t['dp'], t['s']))

rvalue_new_function = C(idn, 'new_function')
spa(rvalue_new_function, lambda t: NewFunction(t['new_function']))

lf_new_resource = C(idn, 'new_resource')
spa(lf_new_resource, lambda t: NewResource(t['new_resource']))


binary = {
    'max': OpMax,
    'min': OpMin,
}

opname = Or([L(x) for x in binary])
max_expr = (C(opname, 'opname') + S(L('(')) +
                C(rvalue, 'op1') + S(L(','))
                + C(rvalue, 'op2')) + S(L(')'))


spa(max_expr, lambda t: binary[t['opname']](t['op1'], t['op2']))

operand = rvalue_new_function ^ rvalue_resource ^ max_expr

# comment_line = S(LineStart()) + ow + L('#') + line + S(EOL)
# comment_line = ow + Literal('#') + line + S(EOL)


simple = (C(idn, 'dp2') + S(L('.')) + C(idn, 's2'))
fancy = (C(idn, 's2') + S(L('provided')) + S(L('by')) + C(idn, 'dp2'))

spa(simple, lambda t: Function(t['dp2'], t['s2']))
spa(fancy, lambda t: Function(t['dp2'], t['s2']))

signal_rvalue = simple | fancy | lf_new_resource | (S(L('(')) + (simple | fancy | lf_new_resource) + S(L(')')))

GEQ = S(L('>=')) 
LEQ = S(L('<='))

constraint_expr = C(signal_rvalue, 'lf') + GEQ + C(rvalue, 'rvalue')
spa(constraint_expr, lambda t: Constraint(t['lf'], t['rvalue']))

constraint_expr2 = C(rvalue, 'rvalue') + LEQ + C(signal_rvalue, 'lf')
spa(constraint_expr2, lambda t: Constraint(t['lf'], t['rvalue']))

line_expr = load_expr ^ constraint_expr ^ constraint_expr2 ^ setname_expr ^ fun_statement ^ res_statement
# dp_statement = S(comment_line) ^ line_expr

dp_model = S(L('cdp')) + S(L('{')) + ZeroOrMore(S(ow) + line_expr) + S(L('}'))


funcname = Combine(idn + ZeroOrMore(L('.') + idn))
code_spec = S(L('code')) + C(funcname, 'function')
spa(code_spec, lambda t: PDPCodeSpec(function=t['function'], arguments={}))



load_pdp = S(L('load')) + C(idn, 'name')
spa(load_pdp, lambda t: LoadDP(t['name']))

pdp_rvalue = load_pdp ^ code_spec


simple_dp_model = (S(L('dp')) + S(L('{')) +
                   C(Group(ZeroOrMore(fun_statement)), 'fun') +
                   C(Group(ZeroOrMore(res_statement)), 'res') +
                   S(L('implemented-by')) + C(pdp_rvalue, 'pdp_rvalue') +
                   S(L('}')))
spa(simple_dp_model, lambda t: DPWrap(list(t[0]), list(t[1]), t[2]))


# dp_rvalue << (load_expr | simple_dp_model) ^ dp_model
dp_rvalue << (load_expr | simple_dp_model | dp_model)


@parse_action
def mult_parse_action(tokens):
    tokens = list(tokens[0])

    bop = Mult
    @contract(tokens='list')
    def parse_op(tokens):
        n = len(tokens)
        if not (n >= 3 and 1 == n % 2):
            msg = 'Expected odd number tokens than %s: %s' % (n, tokens)
            raise DPInternalError(msg)

        if len(tokens) == 3:
            assert tokens[1] == '*'
            return bop(tokens[0], tokens[2])
        else:
            op1 = tokens[0]
            assert tokens[1] == '*'
            op2 = parse_op(tokens[2:])
            return bop(op1, op2)

    res = parse_op(tokens)
    return res

@parse_action
def plus_parse_action(tokens):
    tokens = list(tokens[0])

    @contract(tokens='list')
    def parse_op(tokens):
        n = len(tokens)
        if not (n >= 3 and 1 == n % 2):
            msg = 'Expected odd number tokens than %s: %s' % (n, tokens)
            raise DPInternalError(msg)

        if len(tokens) == 3:
            assert tokens[1] == '+'
            return Plus(tokens[0], tokens[2])
        else:
            op1 = tokens[0]
            assert tokens[1] == '+'
            op2 = parse_op(tokens[2:])
            return Plus(op1, op2)

    res = parse_op(tokens)
    return res


rvalue << operatorPrecedence(operand, [
#     ('-', 1, opAssoc.RIGHT, Unary.parse_action),
    ('*', 2, opAssoc.LEFT, mult_parse_action),
#     ('-', 2, opAssoc.LEFT, Binary.parse_action),
    ('+', 2, opAssoc.LEFT, plus_parse_action),
])


#
# def boxit(s):
#     lines = s.split('\n')
#     W = max(map(len, lines))
# #     c = ['┌', '┐', '└', '┘']
#     s = '┌' + '┄' * (W + 2) + '┐'
#     s += '\n' + '┆ ' + ' ' * (W) + ' ┆'
#
#     for l in lines:
#         s += '\n┆ ' + l.ljust(W, '-') + ' ┆'
#     s += '\n' + '┆ ' + ' ' * (W) + ' ┆'
#     s += '\n' + '└' + '┄' * (W + 2) + '┘'
#
#     return s

def parse_wrap(expr, string):
    string = string.strip()
    # m = boxit
    m = lambda x: x
    try:
        return expr.parseString(string, parseAll=True)
    except (ParseException, ParseFatalException) as e:
        where = Where(string, line=e.lineno, column=e.col)
        raise DPSyntaxError(str(e), where=where)
    except DPSemanticError as e:
        msg = "User error while interpreting the model:"
        msg += "\n\n" + indent(m(string), '  ') + '\n'
        raise_wrapped(DPSemanticError, e, msg, compact=True)
    except DPInternalError as e:
        msg = "Internal error while evaluating the spec:"
        msg += "\n\n" + indent(m(string), '  ') + '\n'
        raise_wrapped(DPInternalError, e, msg, compact=False)
    
def remove_comments(s):
    lines = s.split("\n")
    def remove_comment(line):
        if '#' in line:
            return line[:line.index('#')]
        else:
            return line
    return "\n".join(map(remove_comment, lines))

@contract(returns=NamedDP)
def parse_model(string):
    string = remove_comments(string)
    res = parse_wrap(dp_model, string)[0]
    return res

def parse_line(line):
    return parse_wrap(line_expr, line)[0]

@parse_action
def dp_model_parse_action(tokens):
    res = list(tokens)
    if not res:
        raise DPSemanticError('Empty model')
    from mocdp.lang.blocks import interpret_commands
    return interpret_commands(res)

dp_model.setParseAction(dp_model_parse_action)


