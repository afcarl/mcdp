from contracts.interface import ContractSyntaxError

class DPInternalError(Exception):
    """ Internal consistency errors (not user) """

class DPUserError(Exception):
    pass


class DPSyntaxError(ContractSyntaxError, DPUserError):
    pass

class DPSemanticError(ContractSyntaxError, DPUserError):
    pass

class _storage:
    first = True

from contracts.enabling import all_disabled

def do_extra_checks():

    res = not all_disabled()
    if _storage.first:
        print('do_extra_checks: %s' % res)
    _storage.first = False
    return res

def mcdp_dev_warning(s):
    # warnings.warn(s)
    pass
