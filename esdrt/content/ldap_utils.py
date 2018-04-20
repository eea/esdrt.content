from itertools import chain

from zope.component import getUtility
from esdrt.content.utilities.interfaces import ILDAPQuery
from esdrt.content.utilities.ldap_utils import format_or


def query_group_members(portal, query):
    ldap_plugin = portal['acl_users']['ldap-plugin']['acl_users']
    q_ldap = getUtility(ILDAPQuery)
    q_ldap.connect(ldap_plugin)

    res_groups = q_ldap.query_groups(query, ('uniqueMember', ))
    unique_users = set(chain(*res_groups.values()))
    user_names = q_ldap.query_users(format_or('uid', unique_users), ('cn', ))
    return {
        gname: [user_names[muid] for muid in muids]
        for gname, muids in res_groups.items()
    }
