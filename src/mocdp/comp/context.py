# -*- coding: utf-8 -*-
from collections import namedtuple
from contracts import contract
from contracts.utils import indent, raise_desc, raise_wrapped
from mocdp.exceptions import DPInternalError, DPSemanticError, mcdp_dev_warning
from mocdp.posets import Space
from mocdp.comp.interfaces import NamedDP

__all__ = [
    'Connection',
    'Context',
]

Connection0 = namedtuple('Connection', 'dp1 s1 dp2 s2')
class Connection(Connection0):
    def __repr__(self):
        return ("Constraint(%s.%s <= %s.%s)" %
                (self.dp1, self.s1, self.dp2, self.s2))

    def involves_any_of_these_nodes(self, nodes):
        """ Returns true if any of the two nodes is in the iterable nodes."""
        return self.dp1 in nodes or self.dp2 in nodes


class CFunction():
    @contract(dp=str, s=str)
    def __init__(self, dp, s):
        self.dp = dp
        self.s = s

class CResource():
    @contract(dp=str, s=str)
    def __init__(self, dp, s):
        self.dp = dp
        self.s = s


class ValueWithUnits():

    @contract(unit=Space)
    def __init__(self, value, unit):
        unit.belongs(value)
        self.value = value
        self.unit = unit

    def __repr__(self):
        return 'ValueWithUnits(%r, %r)' % (self.value, self.unit)

class NoSuchMCDPType(Exception):
    pass

def load_ndp_conftools(load_arg):
    from mocdp.configuration import get_conftools_nameddps
    from conf_tools.exceptions import ConfToolsException

    library = get_conftools_nameddps()

    try:
        _, ndp = library.instance_smarter(load_arg)
    except ConfToolsException as e:
        msg = 'Cannot load predefined DP %s.' % load_arg.__repr__()
        raise_wrapped(DPSemanticError, e, msg, compact=True)

    return ndp

class Context():

    def __init__(self):
        self.names = {}  # name -> ndp
        self.connections = []

        self.fnames = []
        self.rnames = []

        self.var2resource = {}  # str -> Resource
        self.var2model = {}  # str -> NamedDP
        self.constants = {}  # str -> ValueWithUnits
        
        self.load_ndp_hooks = [load_ndp_conftools]

    def child(self):
        """ A child context preserves the value of the constants
            and the model types. """
        c = Context()
        c.load_ndp_hooks = self.load_ndp_hooks
        c.var2model.update(self.var2model)
        c.constants.update(self.constants)
        return c

    def load_ndp(self, load_arg):
        errors = []
        for hook in self.load_ndp_hooks:
            try:
                res = hook(load_arg)
                assert isinstance(res, NamedDP)
                return res
            except DPSemanticError as e:
                errors.append(str(e))
        msg = 'Could not load: \n%s' % "\n\n".join(errors)
        raise DPSemanticError(msg)


    @contract(s='str', dp='str', returns=CFunction)
    def make_function(self, dp, s):
        assert isinstance(dp, str)
        if not dp in self.names:
            msg = 'Unknown dp (%r.%r)' % (dp, s)
            raise DPSemanticError(msg)
        return CFunction(dp, s)

    @contract(s='str', dp='str', returns=CResource)
    def make_resource(self, dp, s):
        if not isinstance(dp, str):
            raise DPInternalError((dp, s))
        if not dp in self.names:
            msg = 'Unknown dp (%r.%r)' % (dp, s)
            raise DPSemanticError(msg)

        ndp = self.names[dp]

        if not s in ndp.get_rnames():
            msg = 'Unknown resource %r.' % (s)
            msg += '\nThe design problem %r evaluates to:' % dp
            msg += '\n' + indent(ndp.repr_long(), '  ')
            raise DPSemanticError(msg)

        return CResource(dp, s)

    def _check_good_name(self, name):
        forbidden = ['(', ']', ')', ' ']
        for f in forbidden:
            if f in name:
                raise ValueError(name)

    @contract(name=str)
    def set_var2resource(self, name, value):
        self._check_good_name(name)
        if name in self.var2resource:
            raise ValueError(name)

        self.var2resource[name] = value

    @contract(name=str)
    def set_var2model(self, name, value):
        from mocdp.comp.interfaces import NamedDP
        assert isinstance(value, NamedDP)
        self._check_good_name(name)
        if name in self.var2model:
            raise ValueError(name)
        self.var2model[name] = value

    def get_var2model(self, name):
        if not name in self.var2model:
            msg = 'I cannot find the MCDP type %r.' % name
            msg += '\n Known types: %s' % list(self.var2model)
            msg += '\n Known constants: %s' % list(self.constants)
            msg += '\n Known resources: %s' % list(self.var2resource)
            raise NoSuchMCDPType(msg)
        return self.var2model[name]

    @contract(name=str)
    def set_constant(self, name, value):
        self._check_good_name(name)
        if name in self.var2resource:
            raise ValueError(name)

        self.constants[name] = value

    def info(self, s):
        # print(s)
        pass

    def add_ndp(self, name, ndp):
        self.info('Adding name %r = %r' % (name, ndp))
        if name in self.names:
            # where?
            raise DPSemanticError('Repeated identifier %r.' % name)
        self.names[name] = ndp

    def get_name_for_fun_node(self, name):
        return '_fun_%s' % name

    def add_ndp_fun(self, fname, ndp):
        name = self.get_name_for_fun_node(fname)
        self.info('Adding new function %r as %r.' % (str(name), fname))
        self.add_ndp(name, ndp)
        self.fnames.append(fname)

    def is_new_function(self, name):
        assert name in self.names
        return '_fun_' in name

    def is_new_resource(self, name):
        assert name in self.names
        return '_res_' in name

    def get_name_for_res_node(self, name):
        return '_res_%s' % name

    def add_ndp_res(self, rname, ndp):
        name = self.get_name_for_res_node(rname)
        self.info('Adding new resource %r as %r ' % (str(name), rname))
        self.add_ndp(name, ndp)
        self.rnames.append(rname)

        # self.newresources[rname] = ndp

    def iterate_new_functions(self):
        for fname in self.fnames:
            name = self.get_name_for_fun_node(fname)
            ndp = self.names[name]
            yield fname, name, ndp

    def iterate_new_resources(self):
    # for fname, name, ndp in context.iterate_new_functions():
        for rname in self.rnames:
            name = self.get_name_for_res_node(rname)
            ndp = self.names[name]
            yield rname, name, ndp

    def get_ndp_res(self, rname):
        name = self.get_name_for_res_node(rname)
        if not name in self.names:
            raise ValueError('Resource name %r (%r) not found in %s.' %
                             (rname, name, list(self.names)))
        return self.names[name]

    def get_ndp_fun(self, fname):
        name = self.get_name_for_fun_node(fname)
        if not name in self.names:
            raise ValueError('Function name %r (%r) not found in %s.' %
                             (fname, name, list(self.names)))
        return self.names[name]

    @contract(c=Connection)
    def add_connection(self, c):
        self.info('Adding connection %r' % str(c))
        if not c.dp1 in self.names:
            raise_desc(DPSemanticError, 'Invalid connection: %r not found.' % c.dp1,
                       names=self.names, c=c)

        if not c.dp2 in self.names:
            raise_desc(DPSemanticError, 'Invalid connection: %r not found.' % c.dp2,
                       names=self.names, c=c)

        mcdp_dev_warning('redo this check')

        if self.is_new_function(c.dp2):
            msg = "Cannot add connection to external interface %r." % c.dp1
            raise_desc(DPSemanticError, msg, c=c)

        if self.is_new_resource(c.dp1):
            msg = "Cannot add connection to external interface %r." % c.dp2
            raise_desc(DPSemanticError, msg, c=c)

        # Find if there is already a connection to c.dp2,c.s2
        for c0 in self.connections:
            if c0.dp2 == c.dp2 and c0.s2 == c.s2:
                msg = 'There is already a connection to function %r of %r.' % (c.s2, c.dp2)
                raise_desc(DPSemanticError, msg)

        ndp1 = self.names[c.dp1]
        ndp2 = self.names[c.dp2]

        rnames = ndp1.get_rnames()
        if not c.s1 in rnames:
            msg = "Resource %r does not exist (known: %s)" % (c.s1, ", ".join(rnames))
            raise_desc(DPSemanticError, msg, known=rnames)

        fnames = ndp2.get_fnames()
        if not c.s2 in fnames:
            msg = "Function %r does not exist (known: %s)" % (c.s2, ", ".join(fnames))
            raise_desc(DPSemanticError, msg, known=rnames)


        R1 = ndp1.get_rtype(c.s1)
        F2 = ndp2.get_ftype(c.s2)
        # print('connecting R1 %s to R2 %s' % (R1, F2))
        if not (R1 == F2):
            msg = 'Connection between different spaces'
            raise_desc(DPSemanticError, msg, F2=F2, R1=R1, ndp1=ndp1,
                       ndp2=ndp2)

        self.connections.append(c)

    def new_name(self, prefix):
        for i in range(1, 1000):
            cand = prefix + '%d' % i
            if not cand in self.names:
                return cand
        assert False, 'cannot find name? %r' % cand

    def _fun_name_exists(self, fname):
        for ndp in self.names.values():
            if fname in ndp.get_fnames():
                return True
        return False

    def _res_name_exists(self, rname):
        for ndp in self.names.values():
            if rname in ndp.get_rnames():
                return True
        return False

    def new_fun_name(self, prefix):
        for i in range(1, 1000):
            cand = prefix + '%d' % i
            if not self._fun_name_exists(cand):
                return cand
        assert False, 'cannot find name? %r' % cand

    def new_res_name(self, prefix):
        for i in range(1, 10000):
            cand = prefix + '%d' % i
            if not self._res_name_exists(cand):
                return cand
        assert False, 'cannot find name? %r' % cand

    @contract(a=CResource)
    def get_rtype(self, a):
        """ Gets the type of a resource, raises DPSemanticError if not present. """
        if not a.dp in self.names:
            msg = "Cannot find design problem %r." % str(a)
            raise DPSemanticError(msg)
        dp = self.names[a.dp]
        if not a.s in dp.get_rnames():
            msg = "Design problem %r does not have resource %r." % (a.dp, a.s)
            raise_desc(DPSemanticError, msg, ndp=dp.repr_long())
        return dp.get_rtype(a.s)

    @contract(a=CFunction)
    def get_ftype(self, a):
        """ Gets the type of a function, raises DPSemanticError if not present. """
        if not a.dp in self.names:
            msg = "Cannot find design problem %r." % str(a)
            raise DPSemanticError(msg)
        dp = self.names[a.dp]
        if not a.s in dp.get_fnames():
            msg = "Design problem %r does not have function %r." % (a.dp, a.s)
            raise_desc(DPSemanticError, msg, ndp=dp.repr_long())
        return dp.get_ftype(a.s)

    def get_connections_for(self, name1, name2):
        s = set()
        for c in self.connections:
            if c.dp1 == name1 and c.dp2 == name2:
                s.add(c)
        return s
