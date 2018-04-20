from itertools import chain

from zope.component import getUtility
from esdrt.content.utilities.interfaces import ILDAPQuery
from esdrt.content.utilities.ldap_utils import format_or


def format_users(q_attr, ldap_result):
    return {
        uid.split(',')[0]:
            attr[q_attr][0]
        for uid, attr in ldap_result
    }


def format_groups(q_attr, ldap_result):
    return {
        res[0].split(',')[0][3:]:
            [x.split(',')[0] for x in res[-1][q_attr]]
        for res in ldap_result
    }


def query_group_members(portal, query):
    ldap_plugin = portal['acl_users']['ldap-plugin']['acl_users']
    with getUtility(ILDAPQuery)(ldap_plugin, paged=True) as q_ldap:
        res_groups = format_groups(
            'uniqueMember',
            q_ldap.query_groups(query, ('uniqueMember', ))
        )

        unique_users = set(chain(*res_groups.values()))
        user_names = format_users(
            'cn',
            q_ldap.query_users(
                format_or('', unique_users), ('cn', )
            )
        )

        return {
            gname: [user_names[muid] for muid in muids]
            for gname, muids in res_groups.items()
        }
