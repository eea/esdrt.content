from Acquisition import aq_inner
from Acquisition import aq_parent

from plone import api

from esdrt.content.reviewfolder import IReviewFolder

from esdrt.content.constants import LDAP_SR
from esdrt.content.constants import LDAP_QE
from esdrt.content.constants import LDAP_LR
from esdrt.content.constants import LDAP_RE
from esdrt.content.constants import LDAP_MSA

from esdrt.content.constants import ROLE_RP1
from esdrt.content.constants import ROLE_RP2
from esdrt.content.constants import ROLE_QE
from esdrt.content.constants import ROLE_LR
from esdrt.content.constants import ROLE_MSA


def grant_local_roles(context):
    """ add local roles to the groups when adding an observation
    """
    country = context.country.lower()
    sector = context.ghg_source_category_value()
    applies_to = [context]
    parent = aq_parent(aq_inner(context))
    if IReviewFolder.providedBy(parent):
        applies_to.append(parent)

    context.__ac_local_roles_block__ = True

    qe_lr_split = context.enable_qe_lr_split

    for obj in applies_to:
        _roles_start = obj.get_local_roles()

        if qe_lr_split:
            # New QE split.
            qe_group = "%s-%s-%s" % (LDAP_QE, sector, country)
            lr_group = "%s-%s-%s" % (LDAP_LR, sector, country)
        else:
            # OLD QE support.
            qe_group = "%s-%s" % (LDAP_QE, sector)
            lr_group = "%s-%s" % (LDAP_LR, country)

        rp1_group = "%s-%s-%s" % (LDAP_SR, sector, country)
        rp2_group = "%s-%s-%s" % (LDAP_RE, sector, country)

        msa_group = "%s-%s" % (LDAP_MSA, country)

        api.group.grant_roles(groupname=qe_group, roles=[ROLE_QE], obj=obj)
        api.group.grant_roles(groupname=lr_group, roles=[ROLE_LR], obj=obj)

        api.group.grant_roles(groupname=rp1_group, roles=[ROLE_RP1], obj=obj)
        api.group.grant_roles(groupname=rp2_group, roles=[ROLE_RP2], obj=obj)

        api.group.grant_roles(groupname=msa_group, roles=[ROLE_MSA], obj=obj)

        _roles_end = obj.get_local_roles()
        # Reindex only if roles were changed.
        if _roles_end != _roles_start:
            obj.reindexObjectSecurity()
