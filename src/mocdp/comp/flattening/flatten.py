# -*- coding: utf-8 -*-
from contracts import contract
from contracts.interface import add_prefix
from contracts.utils import raise_desc
from mocdp.comp.composite import CompositeNamedDP
from mocdp.comp.context import (Connection, get_name_for_fun_node,
    get_name_for_res_node, is_fun_node_name, is_res_node_name)
from mocdp.comp.wrap import SimpleWrap
from mocdp.exceptions import mcdp_dev_warning
from mocdp.ndp.named_coproduct import NamedDPCoproduct

__all__ = [
    'cndp_flatten',
    'flatten_add_prefix',
]

sep = '/'

def flatten_add_prefix(ndp, prefix):
    """ Adds a prefix for every node name and to functions/resources. """

    if isinstance(ndp, SimpleWrap):
        dp = ndp.get_dp()
        fnames = ['%s%s%s' % (prefix, sep, _) for _ in ndp.get_fnames()]
        rnames = ['%s%s%s' % (prefix, sep, _) for _ in ndp.get_rnames()]
        icon = ndp.icon
        if len(fnames) == 1: fnames = fnames[0]
        if len(rnames) == 1: rnames = rnames[0]
        sw = SimpleWrap(dp, fnames=fnames, rnames=rnames, icon=icon)
        return sw
    
    if isinstance(ndp, CompositeNamedDP):
        
        def get_new_name(name2):
            isf, fname = is_fun_node_name(name2)
            isr, rname = is_res_node_name(name2)

            if isf:
                return get_name_for_fun_node('%s%s%s' % (prefix, sep, fname))
            elif isr:
                return get_name_for_res_node('%s%s%s' % (prefix, sep, rname))
            else:
                return "%s%s%s" % (prefix, sep, name2)
            
        def transform(name2, ndp2):
            # Returns name, ndp
            isf, fname = is_fun_node_name(name2)
            isr, rname = is_res_node_name(name2)
            
            if isf:
                dp = ndp2.dp
                fnames = "%s%s%s" % (prefix, sep, fname)
                rnames = "%s%s%s" % (prefix, sep, fname)
                ndp = SimpleWrap(dp=dp, fnames=fnames, rnames=rnames, icon=ndp2.icon)
            elif isr:
                dp = ndp2.dp
                fnames = "%s%s%s" % (prefix, sep, rname)
                rnames = "%s%s%s" % (prefix, sep, rname)
                ndp = SimpleWrap(dp=dp, fnames=fnames, rnames=rnames, icon=ndp2.icon)
            else:
                ndp = flatten_add_prefix(ndp2, prefix)
            return ndp


        names2 = {}
        connections2 = set()
        for name2, ndp2 in ndp.get_name2ndp().items():
            name_ = get_new_name(name2)
            ndp_ = transform(name2, ndp2)
            assert not name_ in names2
            names2[name_] = ndp_
        
        for c in ndp.get_connections():
            dp1, s1, dp2, s2 = c.dp1, c.s1, c.dp2, c.s2
            dp1 = get_new_name(dp1)
            dp2 = get_new_name(dp2)
            s1_ = "%s%s%s" % (prefix, sep, s1)
            s2_ = "%s%s%s" % (prefix, sep, s2)
            assert s1_ in names2[dp1].get_rnames()
            assert s2_ in names2[dp2].get_fnames()
            c2 = Connection(dp1=dp1, s1=s1_, dp2=dp2, s2=s2_)
            connections2.add(c2)
            
        fnames2 = ['%s%s%s' % (prefix, sep, _) for _ in ndp.get_fnames()]
        rnames2 = ['%s%s%s' % (prefix, sep, _) for _ in ndp.get_rnames()]

        return CompositeNamedDP.from_parts(names2, connections2, fnames2, rnames2)

    # XXX
    # mocdp.ndp.named_coproduct.NamedDPCoproduct
    if isinstance(ndp, NamedDPCoproduct):
        children = ndp.ndps
        children2 = tuple([flatten_add_prefix(_, prefix) for _ in children])
        labels2 = ndp.labels
        return NamedDPCoproduct(children2, labels2)

    assert False, ndp
    
@contract(ndp=CompositeNamedDP)
def cndp_flatten(ndp):
    name2ndp = ndp.get_name2ndp()
    connections = ndp.get_connections()
    fnames = ndp.get_fnames()
    rnames = ndp.get_rnames()
    names2 = {}
    connections2 = set()

    for name, n0 in name2ndp.items():
        n1 = n0.flatten()
        # print('n1: %s' % add_prefix(str(n1), '| '))

        if isinstance(n1, CompositeNamedDP):
            nn = flatten_add_prefix(n1, prefix=name)
            # print('nn: %s' % add_prefix(str(nn), '| '))
        else:
            nn = n1

        if isinstance(nn, CompositeNamedDP):
            for name2, ndp2 in nn.get_name2ndp().items():
                assert not name2 in names2
                names2[name2] = ndp2
            
            for c in nn.get_connections():
                dp1, s1, dp2, s2 = c.dp1, c.s1, c.dp2, c.s2

                assert s1 in names2[dp1].get_rnames()
                assert s2 in names2[dp2].get_fnames()
                c2 = Connection(dp1=dp1, s1=s1, dp2=dp2, s2=s2)
                connections2.add(c2)
        else:
            names2[name] = nn

    for c in connections:
        dp2 = c.dp2
        s2 = c.s2
        dp1 = c.dp1
        s1 = c.s1

        dp2_was_exploded = isinstance(name2ndp[dp2], CompositeNamedDP)
        if dp2_was_exploded:
            dp2_ = "_fun_%s%s%s" % (dp2, sep, s2)
            if not dp2_ in names2:
                raise_desc(AssertionError, "?", dp2_=dp2_, c=c, names2=sorted(names2))
            s2_ = '%s%s%s' % (dp2, sep, s2)
        else:
            dp2_ = dp2
            s2_ = s2

        dp1_was_exploded = isinstance(name2ndp[dp1], CompositeNamedDP)
        if dp1_was_exploded:
            dp1_ = "_res_%s%s%s" % (dp1, sep, s1)
            if not dp1_ in names2:
                raise_desc(AssertionError, "?", dp1_=dp1_, c=c, names2=sorted(names2))
            s1_ = '%s%s%s' % (dp1, sep, s1)
        else:
            dp1_ = dp1
            s1_ = s1

        assert dp1_ in names2

        assert s1_ in names2[dp1_].get_rnames() , (s1_, names2[dp1_].get_rnames())

        assert dp2_ in names2
        assert s2_ in names2[dp2_].get_fnames(), (s2_, names2[dp2_].get_fnames())

        c2 = Connection(dp1=dp1_, s1=s1_, dp2=dp2_, s2=s2_)
        # (dp2, s2)
        connections2.add(c2)

    return CompositeNamedDP.from_parts(names2, connections2, fnames, rnames)
