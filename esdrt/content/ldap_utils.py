""" Utility functions to query LDAP directly. Bypassing Plone bloat.
"""

from itertools import chain
import ldap


def format_or(items):
    """ Turns ['uid=a', 'uid=b', 'uid=c']
        into (|(uid=a)(uid=b)(uid=c)).
    """
    with_parens = ['({})'.format(item) for item in items]
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
    l = ldap.initialize(host)

    if auth:
        l.simple_bind_s(config['user'], config['pwd'])
    else:
        l.simple_bind_s('', '')

    return l


def query_users(ou, l, query):
    result = l.search_s(ou, ldap.SCOPE_SUBTREE, query, ['cn'])
    return {uid.split(',')[0]: attr['cn'][0] for uid, attr in result}


def query_groups(ou, l, query):
    result = l.search_s(ou, ldap.SCOPE_SUBTREE, query, ['uniqueMember'])
    return {
        res[0].split(',')[0][3:]:
        [x.split(',')[0] for x in res[-1]['uniqueMember']]
        for res in result
    }


def query_group_members(config, l, query):
    res_groups = query_groups(config['ou_groups'], l, query)
    unique_users = set(chain(*res_groups.values()))
    user_names = query_users(config['ou_users'], l, format_or(unique_users))
    return {
        gname: [user_names[muid] for muid in muids]
        for gname, muids in res_groups.items()
    }
