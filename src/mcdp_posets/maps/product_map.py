from mcdp_posets import Map
from contracts import contract
from mocdp.exceptions import mcdp_dev_warning
from mcdp_posets import SpaceProduct


class ProductMap(Map):
    @contract(fs='seq[>=1]($Map)')
    def __init__(self, fs):
        fs = tuple(fs)
        self.fs = fs
        mcdp_dev_warning('add promotion to SpaceProduct')
        dom = SpaceProduct(tuple(fi.get_domain() for fi in fs))
        cod = SpaceProduct(tuple(fi.get_codomain() for fi in fs))
        Map.__init__(self, dom=dom, cod=cod)

    def _call(self, x):
        x = tuple(x)
        return tuple(fi(xi) for fi, xi in zip(self.fs, x))
