""" Utility functions to query LDAP directly. Bypassing Plone bloat.
"""
import logging
import ldap
from ldap.controls import SimplePagedResultsControl
from functools import partial

LOG = logging.getLogger('esdrt.content.ILDAPQuery')

PAGESIZE = 1000


def format_or(prefix, items):
    """ Turns 'uid', ['a', 'b', 'c']
        into (|(uid=a)(uid=b)(uid=c)).
    """
    formatter = (
        partial('({}={})'.format, prefix)
        if prefix else
        '({})'.format
    )
    with_parens = map(formatter, items)
    return '(|{})'.format(''.join(with_parens))


def get_config(acl):
    return dict(
        ou_users=acl.users_base,
        ou_groups=acl.groups_base,
        user=acl._binduid,
        pwd=acl._bindpwd,
        hosts=acl._delegate.getServers(),
    )


def connect(config, auth=False):
    hosts = config['hosts']

    if not hosts:
        raise ValueError('No LDAP host configured!')

    # connect to the first configured host
    host = '{protocol}://{host}:{port}'.format(**hosts[0])
    conn = ldap.initialize(host)

    if auth:
        conn.simple_bind_s(config['user'], config['pwd'])
    else:
        conn.simple_bind_s('', '')

    return conn


def paged_query(ou, l, lc, query, attrs):
    cur_page = 0
    while True:
        cur_page += 1
        LOG.info('Requesting page %d!', cur_page)
        # request a page
        msgid = l.search_ext(
            ou, ldap.SCOPE_SUBTREE, query, attrs,
            serverctrls=[lc]
        )
        # retrieve results
        rtype, rdata, rmsgid, serverctrls = l.result3(msgid)

        # output results
        for dn, attrs in rdata:
            yield dn, attrs

        # retrieve paging controls
        pctrl = next(
            x for x in serverctrls
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

    acl = None
    config = None
    paged = False
    pagesize = PAGESIZE
    connection = None

    def __call__(self, acl, paged=False, pagesize=PAGESIZE):
        """ acl needs to be a LDAPUserFolder instance.
        """
        self.acl = acl
        self.config = get_config(acl)
        self.paged = paged
        self.pagesize = pagesize
        self.connection = connect(self.config, auth=True)
        return self

    def _query_ou_paged(self, ou, query, attrs):
        pagesize = self.pagesize
        LOG.info('Paged query requested. Batch size: %d', pagesize)
        lc = SimplePagedResultsControl(True, size=pagesize, cookie='')
        return [x for x in paged_query(ou, self.connection, lc, query, attrs)]

    def _query_ou(self, ou, query, attrs):
        return self.connection.search_s(ou, ldap.SCOPE_SUBTREE, query, attrs)

    def query_ou(self, *args):
        meth = self._query_ou_paged if self.paged else self._query_ou
        return meth(*args)

    def query_groups(self, query, attrs=tuple()):
        return self.query_ou(self.config['ou_groups'], query, attrs)

    def query_users(self, query, attrs=tuple()):
        return self.query_ou(self.config['ou_users'], query, attrs)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        """ Method called when used in an `with` block.
            This object is used as an utility, which means there is only
            one instance available. Cleanup on exit.
        """
        self.connection.unbind()
        self.connection = None
        self.acl = None
        self.config = None
        self.paged = False
        self.pagesize = PAGESIZE
