from functools import partial
from itertools import chain
from itertools import product


from zope.component.hooks import getSite

from esdrt.content.setuphandlers import LDAP_PLUGIN_ID

from esdrt.content.utilities import ldap_utils

from esdrt.content.constants import LDAP_SR
from esdrt.content.constants import LDAP_QE
from esdrt.content.constants import LDAP_RE
from esdrt.content.constants import LDAP_LR
from esdrt.content.constants import LDAP_MSA

from esdrt.content.constants import ROLE_RP1
from esdrt.content.constants import ROLE_RP2
from esdrt.content.constants import ROLE_QE
from esdrt.content.constants import ROLE_LR
from esdrt.content.constants import ROLE_MSA


QUERY_LDAP_ROLES = ldap_utils.format_or(
    'cn', (
        LDAP_SR + '-sector*-*',
        LDAP_QE + '-sector*',
        LDAP_RE + '-sector*-*',
        LDAP_LR + '-*',
        LDAP_MSA + '-*',

    )
)


def f_start(pat, s):
    return s.startswith(pat)


f_start_sr = partial(f_start, LDAP_SR)
f_start_qe = partial(f_start, LDAP_QE)
f_start_re = partial(f_start, LDAP_RE)
f_start_lr = partial(f_start, LDAP_LR)
f_start_msa = partial(f_start, LDAP_MSA)


def setup_reviewfolder_roles(folder):
    site = getSite()
    acl = site["acl_users"][LDAP_PLUGIN_ID]

    with ldap_utils.get_query_utility()(acl, paged=True) as q_ldap:
        q_groups = q_ldap.query_groups(QUERY_LDAP_ROLES, ('cn',))

    groups = [r[1]['cn'][0] for r in q_groups]

    grant = chain(
        product([ROLE_RP1], list(filter(f_start_sr, groups))),
        product([ROLE_QE], list(filter(f_start_qe, groups))),
        product([ROLE_RP2], list(filter(f_start_re, groups))),
        product([ROLE_LR], list(filter(f_start_lr, groups))),
        product([ROLE_MSA], list(filter(f_start_msa, groups))),
    )

    for role, g_name in grant:
        folder.manage_setLocalRoles(g_name, [role])

    return folder


class SetupReviewFolderRoles(object):
    def __call__(self, folder):
        return setup_reviewfolder_roles(folder)
