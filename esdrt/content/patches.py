from Products.CMFDiffTool import dexteritydiff
from eea.cache import cache

EXCLUDED_FIELDS = list(dexteritydiff.EXCLUDED_FIELDS)
EXCLUDED_FIELDS.append('ghg_estimations')
dexteritydiff.EXCLUDED_FIELDS = tuple(EXCLUDED_FIELDS)

from logging import getLogger
log = getLogger(__name__)
log.info('Patching difftool excluded fields to add ghg_estimations')


def _cachekey_lookupuserbyattr(meth, self, *args, **kwargs):
    return (meth.__name__, self.__name__, args, kwargs.items())


@cache(_cachekey_lookupuserbyattr)
def _lookupuserbyattr_cache_wrapper(meth, *args, **kwargs):
    """ Wrapper to raise error when login was not successfull.
        Needed to avoid caching unsuccessfull login attempts.
    """
    result = meth(*args, **kwargs)
    if not any(result):
        raise ValueError(result)
    return result


def _lookupuserbyattr(self, *args, **kwargs):
    try:
        return _lookupuserbyattr_cache_wrapper(
            self._old__lookupuserbyattr, *args, **kwargs)
    except ValueError as exc:
        return exc.message


def _cachekey_LDAPDelegate_search(meth, self, *args, **kwargs):
    kw = tuple([(k, v) for k, v in kwargs.items() if k != 'bind_pwd'])
    return (meth.__name__, self.__name__, args, kw)


@cache(_cachekey_LDAPDelegate_search)
def LDAPDelegate_search_cache_wrapper(meth, *args, **kwargs):
    """ Wrapper to avoid cache when there is an
        error in the query result.
    """
    result = meth(*args, **kwargs)

    if result['exception']:
        raise ValueError(result)

    return result


def LDAPDelegate_search(self, *args, **kwargs):
    try:
        return LDAPDelegate_search_cache_wrapper(
            self._old_search, *args, **kwargs)
    except ValueError as exc:
        return exc.message
