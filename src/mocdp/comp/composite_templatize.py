from contracts import contract
from mocdp.comp.wrap import SimpleWrap
from mcdp_posets.poset_product import PosetProduct
from mocdp.comp.composite import CompositeNamedDP
from mocdp.comp.interfaces import NamedDP
from mocdp.ndp.named_coproduct import NamedDPCoproduct

def cndp_templatize_children(cndp):
    """ Replaces all sub composites with the corresponding template """
    assert isinstance(cndp, CompositeNamedDP), cndp
    fnames = cndp.get_fnames()
    rnames = cndp.get_rnames()
    connections = cndp.get_connections()

    def filter_child(child):
        if isinstance(child, CompositeNamedDP):
            return ndp_templatize(child)
        elif isinstance(child, NamedDPCoproduct):
            return ndpcoproduct_templatize(child)
        else:
            return child

    name2ndp = dict([(k, filter_child(v)) for k, v in cndp.get_name2ndp().items()])

    return CompositeNamedDP.from_parts(name2ndp, connections, fnames, rnames)

def ndpcoproduct_templatize(ndp):
    ndps = tuple([ndp_templatize(c) for c in ndp.ndps])
    labels = ndp.labels
    res = NamedDPCoproduct(ndps=ndps, labels=labels)
    # attr_load_name?
    return res


@contract(ndp=NamedDP, returns=SimpleWrap)
def ndp_templatize(ndp, mark_as_template=False):
    """ Creates a template based on the interface. 
    
        Copies attributes: ATTR_LOAD_NAME
    """
    fnames = ndp.get_fnames()
    ftypes = ndp.get_ftypes(fnames)
    rnames = ndp.get_rnames()
    rtypes = ndp.get_rtypes(rnames)

    if len(fnames) == 1:
        fnames = fnames[0]
        F = ftypes[0]
    else:
        F = PosetProduct(tuple(ftypes))

    if len(rnames) == 1:
        rnames = rnames[0]
        R = rtypes[0]
    else:
        R = PosetProduct(tuple(rtypes))

    from mocdp.comp.template_imp import Dummy

    dp = Dummy(F, R)
    if mark_as_template:
        klass = OnlyTemplate
    else:
        klass = SimpleWrap
    res = klass(dp, fnames, rnames)

    from mcdp_library.library import ATTR_LOAD_NAME
    if hasattr(ndp, ATTR_LOAD_NAME):
        x = getattr(ndp, ATTR_LOAD_NAME)
        setattr(res, ATTR_LOAD_NAME, x)
    return res


class OnlyTemplate(SimpleWrap):
    pass


