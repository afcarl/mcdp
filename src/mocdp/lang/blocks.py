from .parts import Constraint, LoadCommand, SetName
from contracts import describe_value
from contracts.utils import raise_desc, raise_wrapped
from mocdp.comp.connection import Connection
from mocdp.comp.wrap import dpwrap
from mocdp.configuration import get_conftools_nameddps
from mocdp.dp.dp_identity import Identity
from mocdp.dp.dp_sum import Product
from mocdp.posets.rcomp import Rcomp

class Context():
    def __init__(self):
        self.names = {}
        self.connections = []

    def add_ndp(self, name, ndp):
        if name in self.names:
            raise ValueError('Already know %r' % name)
        self.names[name] = ndp

    def add_connection(self, c):
        if not c.dp1 in self.names:
            raise_desc(ValueError, 'Invalid connection', names=self.names, c=c)

        self.names[c.dp1].rindex(c.s1)

        if not c.dp2 in self.names:
            raise_desc(ValueError, 'Invalid connection', names=self.names, c=c)

        self.names[c.dp2].findex(c.s2)

        self.connections.append(c)

    def new_name(self, prefix):
        for i in range(1, 10):
            cand = prefix + '%d' % i
            if not cand in self.names:
                return cand
        assert False

def interpret_commands(res):
    context = Context()
    
    for r in res:
        if isinstance(r, Connection):
            context.add_connection(r)

        elif isinstance(r, Constraint):
            resource = eval_rvalue(r.rvalue, context)
            c = Connection(dp1=resource.dp, s1=resource.s, dp2=r.dp2, s2=r.s2)
            context.add_connection(c)
            
        elif isinstance(r, SetName):
            name = r.name
            ndp = eval_dp_rvalue(r.dp_rvalue, context)
            context.add_ndp(name, ndp)

        else:
            raise ValueError('Cannot interpret %s' % describe_value(r))

    from mocdp.comp import dpgraph
    try:
        return dpgraph(context.names, context.connections)
    except Exception as e:
        raise_wrapped(Exception, e, 'cannot create',
                      names=context.names, connection=context.connections)

def eval_dp_rvalue(r, context):  # @UnusedVariable
    library = get_conftools_nameddps()
    if isinstance(r, LoadCommand):
        load_arg = r.load_arg
        _, ndp = library.instance_smarter(load_arg)
        return ndp
    
    raise ValueError('Invalid dprvaue: %s' % r)

# @contract(returns=Resource)
def eval_rvalue(rvalue, context):
    from .parts import Resource, Mult, NewFunction

    if isinstance(rvalue, Resource):
        return rvalue

    if isinstance(rvalue, Mult):
        a = eval_rvalue(rvalue.a, context)
        b = eval_rvalue(rvalue.b, context)
        F1 = Rcomp()
        F2 = Rcomp()
        R = Rcomp()
        ndp = dpwrap(Product(F1, F2, R), ['a', 'b'], 'res')
        name = context.new_name('mult')
        c1 = Connection(dp1=a.dp, s1=a.s, dp2=name, s2='a')
        c2 = Connection(dp1=b.dp, s1=b.s, dp2=name, s2='b')
        context.add_ndp(name, ndp)
        context.add_connection(c1)
        context.add_connection(c2)
        return Resource(name, 'res')

    if isinstance(rvalue, NewFunction):
        F = Rcomp()
        ndp = dpwrap(Identity(F), rvalue.name, 'a')
        name = context.new_name('id')
        context.add_ndp(name, ndp)
        return Resource(name, 'a')

    raise ValueError(rvalue)


