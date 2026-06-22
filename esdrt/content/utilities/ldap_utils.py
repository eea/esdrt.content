"""Utility functions to query LDAP directly. Bypassing Plone bloat."""
import logging
from functools import partial
from typing import Tuple
from typing import TypedDict

import ldap
import ldapurl
from ldap.controls import SimplePagedResultsControl
from ldap.ldapobject import LDAPObject
from pas.plugins.ldap.plugin import LDAPPlugin

from zope.component import getUtility

from esdrt.content.utilities.interfaces import ILDAPQuery
from esdrt.content.patches import _cachekey, cache

LOG = logging.getLogger("esdrt.content.ILDAPQuery")

PAGESIZE = 1000


class ConfigDict(TypedDict):
    """Type definition for get_config."""

    ou_users: str
    ou_groups: str
    user: str
    pwd: str
    server: str


LDAPAttrs = Tuple[str]


def format_or(prefix, items):
    """Turns 'uid', ['a', 'b', 'c'] into (|(uid=a)(uid=b)(uid=c))."""
    formatter = partial("({}={})".format, prefix) if prefix else "({})".format
    with_parens = list(map(formatter, items))
    return "(|{})".format("".join(with_parens))


def get_config(acl: LDAPPlugin) -> ConfigDict:
    """Retrieve config from a LDAP Plugin."""
    settings = acl.settings
    return dict(
        ou_users=settings["users.baseDN"],
        ou_groups=settings["groups.baseDN"],
        user=settings["server.user"],
        pwd=settings["server.password"],
        server=settings["server.uri"],
    )


def connect(config: ConfigDict, auth=False):
    """Connect based on given config."""
    server = config["server"]

    if not server:
        raise ValueError("No LDAP server configured!")

    conn = ldap.initialize(server)

    if auth:
        conn.simple_bind_s(config["user"], config["pwd"])
    else:
        conn.simple_bind_s("", "")

    return conn


def paged_query(ou, connection, lc: SimplePagedResultsControl, query, attrs):
    cur_page = 0
    while True:
        cur_page += 1
        LOG.info("Requesting page %d!", cur_page)
        # request a page
        msgid = connection.search_ext(
            ou, ldapurl.LDAP_SCOPE_SUBTREE, query, attrs, serverctrls=[lc]
        )
        # retrieve results
        rtype, rdata, rmsgid, serverctrls = connection.result3(msgid)

        # output results
        for dn, attrs in rdata:
            yield dn, attrs

        # retrieve paging controls
        pctrl = next(
            x
            for x in serverctrls
            if x.controlType == SimplePagedResultsControl.controlType
        )

        # If there's a paging cookie, then there are more results
        # update the paged control with the cookie. Next page will
        # be requested on the next loop pass.
        cookie = pctrl.cookie
        if cookie:
            lc.cookie = cookie
        else:
            # no more pages, exit the loop
            break


class LDAPQuery(object):
    """Query LDAP."""

    __name__ = "LDAPQuery"

    acl: LDAPPlugin
    config: ConfigDict
    paged: bool = False
    pagesize: int = PAGESIZE
    connection: LDAPObject

    def __call__(self, acl: LDAPPlugin, paged=False, pagesize: int = PAGESIZE):
        """Initialize the query.

        acl needs to be a LDAPUserFolder instance.
        """
        self.acl = acl
        self.config = get_config(acl)
        self.paged = paged
        self.pagesize = pagesize
        self.connection = connect(self.config, auth=True)
        return self

    def _query_ou_paged(self, ou, query, attrs):
        pagesize = self.pagesize
        LOG.info("Paged query requested. Batch size: %d", pagesize)
        lc = SimplePagedResultsControl(True, size=pagesize, cookie="")
        return [x for x in paged_query(ou, self.connection, lc, query, attrs)]

    def _query_ou(self, ou: str, query: str, attrs):
        return self.connection.search_s(
            ou, ldapurl.LDAP_SCOPE_SUBTREE, query, attrs
        )

    @cache(_cachekey)
    def query_ou(self, *args):
        """Use paged or unpaged search."""
        meth = self._query_ou_paged if self.paged else self._query_ou
        return meth(*args)

    def query_groups(self, query, attrs: LDAPAttrs = tuple()):
        """Search groups."""
        return self.query_ou(self.config["ou_groups"], query, attrs)

    def query_users(self, query, attrs: LDAPAttrs = tuple()):
        """Search users."""
        return self.query_ou(self.config["ou_users"], query, attrs)

    def __enter__(self):
        """Used for `with` block."""
        return self

    def __exit__(self, type, value, traceback):
        """Method called when used in an `with` block.

        This object is used as an utility, which means there is only
        one instance available. Cleanup on exit.
        """
        self.connection.unbind()
        del self.connection
        del self.acl
        del self.config
        self.paged = False
        self.pagesize = PAGESIZE


def get_query_utility() -> LDAPQuery:
    """Get ILDAPQuery utility.

    Wrapper used for type checking.
    """
    return getUtility(ILDAPQuery)
