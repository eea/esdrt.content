""" Utility functions to query LDAP directly. Bypassing Plone bloat.
"""

import ldap
from functools import partial


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


class LDAPQuery(object):

    acl = None
    config = None
    connection = None

    def connect(self, acl):
        """ acl needs to be a LDAPUserFolder instance.
        """
        self.acl = acl
        self.config = get_config(acl)
        self.connection = connect(self.config, auth=True)
        return self.connection

    def query_ou(self, ou, query, attrs):
        if not self.connection:
            raise ValueError('No connection. Run connect() first!')
        return self.connection.search_s(ou, ldap.SCOPE_SUBTREE, query, attrs)

    def query_groups(self, query, attrs=tuple()):
        return self.query_ou(self.config['ou_groups'], query, attrs)

    def query_users(self, query, attrs=tuple()):
        return self.query_ou(self.config['ou_users'], query, attrs)
