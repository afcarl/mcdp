# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from contracts import contract
from contracts import raise_wrapped
from .space_meta import SpaceMeta
from mocdp.exceptions import do_extra_checks

class NotBelongs(Exception):
    pass

class NotEqual(Exception):
    pass

class Uninhabited(Exception):
    ''' There is no element in this space. Raised by witness().'''
    pass

class Space(object):
    __metaclass__ = SpaceMeta

    def format(self, x):
        """ Formats a point in the space. """
        return x.__repr__()

    @abstractmethod
    def belongs(self, x):
        pass

    @abstractmethod
    def check_equal(self, x, y):
        # Raise NotEqual if not
        pass

    def equal(self, a, b):
        try:
            self.check_equal(a, b)
        except NotEqual:
            return False
        else:
            return True
        
    def witness(self):
        """ Returns an element of the space, or raise Uninhabited
            if the space is empty. """
        raise NotImplementedError(type(self))

class Map():

    __metaclass__ = ABCMeta

    def __init__(self, dom, cod):
        self.dom = dom
        self.cod = cod

    @contract(returns=Space)
    def get_domain(self):
        return self.dom

    @contract(returns=Space)
    def get_codomain(self):
        return self.cod

    def __call__(self, x):
        D = self.get_domain()
        if do_extra_checks():
            try:
                D.belongs(x)
            except NotBelongs as e:
                msg = 'Point does not belong to domain.'
                raise_wrapped(NotBelongs, e, msg, map=self, x=x, domain=D)

        y = self._call(x)

        if do_extra_checks():

            C = self.get_codomain()
            try:
                C.belongs(y)
            except NotBelongs as e:
                msg = 'Point does not belong to codomain.'
                raise_wrapped(NotBelongs, e, msg, map=self, y=y, codomain=C)

        return y

    @abstractmethod
    def _call(self, x):
        pass

    def __repr__(self):
        return "%s:%s→%s" % (type(self).__name__,
                             self.get_domain(), self.get_codomain())
