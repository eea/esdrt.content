from itertools import chain

from esdrt.content.setuphandlers import LDAP_PLUGIN_ID
from esdrt.content.utilities import ldap_utils
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
    acl = portal['acl_users'][LDAP_PLUGIN_ID]
    with ldap_utils.get_query_utility()(acl, paged=True) as q_ldap:
        res_groups = format_groups(
            'uniqueMember',
            q_ldap.query_groups(query, ('uniqueMember', ))
        )

        unique_users = [v for v in set(chain(*list(res_groups.values()))) if v]
        user_names = format_users(
            'cn',
            q_ldap.query_users(
                format_or('', unique_users), ('cn', )
            )
        )

        return {
            gname: [user_names[muid] for muid in muids if muid]
            for gname, muids in list(res_groups.items())
        }
