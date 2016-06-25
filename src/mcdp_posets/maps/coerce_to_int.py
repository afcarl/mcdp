from contracts import contract
from mcdp_posets import Map, Space


class CoerceToInt(Map):

    @contract(cod=Space, dom=Space)
    def __init__(self, cod, dom):
        # todo: check dom is Nat or Int
        Map.__init__(self, cod, dom)

    def _call(self, x):
        return int(x)
